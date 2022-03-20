import json
import uuid
from string import Template

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

from graphql_api.models import Table, Column, Relationship


def update_schema(request):
    transport = RequestsHTTPTransport(
        url=f'{settings.METADATA_SERVER_ADDR}/api/graphql/',  # FIXME
        headers={'X-DataHub-Actor': 'urn:li:corpuser:datahub'})

    client = Client(transport=transport)

    query = '''
        {
          search(input: {type: DATASET, query: "$tag", start: $start, count: 1}) {
            start
            count
            total
            searchResults {
              entity {
                urn
                ... on Dataset {
                  name
                  tags {
                    tags {
                      tag {
                        urn
                      }
                    }
                  }
                  schemaMetadata {
                    fields {
                      fieldPath
                    }
                  }
                }
              }  
            }
          }
        }
    '''

    start = 0
    schemas_info = []

    while True:
        schema_info = []
        query_sub = Template(query).safe_substitute(start=start, tag=settings.DWD_API_TAGS['ingestion'])

        result = client.execute(gql(query_sub))

        start = result['search']['start']
        count = result['search']['count']
        total = result['search']['total']

        for searchResult in result['search']['searchResults']:
            entity_urn = searchResult['entity']['urn']
            entity_name = searchResult['entity']['name']
            entity_tags = searchResult['entity']['tags']['tags']
            entity_fields = searchResult['entity']['schemaMetadata']['fields']

            tags = [tag['tag']['urn'] for tag in entity_tags]
            columns = [entity_field['fieldPath'] for entity_field in entity_fields]

            schema_info.append(entity_urn)
            schema_info.append(entity_name)
            schema_info.append(tags)
            schema_info.append(columns)

        schemas_info.append(schema_info)

        if start + count >= total:
            break

        start += count

    # 更新
    update_tables = Table.objects.filter(pk__in=[schema[0] for schema in schemas_info])

    def get_schema(urn):
        for schema in schemas_info:
            if schema[0] == urn:
                return schema

    for ut in update_tables:
        schema = get_schema(ut.urn)
        ut.tags = ', '.join([tag.split(':')[-1] for tag in schema[2]])

        ut.column_set.all().delete()

        add_columns = []
        for column in schema[3]:
            add_columns.append(Column(
                table=ut,
                name=column
            ))
        Column.objects.bulk_create(add_columns)

    Table.objects.bulk_update(update_tables, ['tags'])

    # 新增
    add_schemas = []
    for schema in schemas_info:
        if schema[0] not in [ut.urn for ut in update_tables]:
            add_schemas.append(schema)

    add_tables = []
    add_columns = []
    for schema in add_schemas:
        table = Table(
            urn=schema[0],
            name=schema[1],
            alias=''.join([word[0] for word in schema[1].split('.')[-1].split('_')]) + f'_{str(uuid.uuid1())[:8]}',
            tags=', '.join([tag.split(':')[-1] for tag in schema[2]])
        )
        add_tables.append(table)

        for column in schema[3]:
            add_columns.append(Column(
                table=table,
                name=column
            ))

    Table.objects.bulk_create(add_tables)
    Column.objects.bulk_create(add_columns)

    return HttpResponse()


@csrf_exempt
def update_schema_v2(request):
    schemas = json.loads(request.body)

    def get_schema(relation_name):
        for schema in schemas:
            if schema['relation_name'] == relation_name:
                return schema

    def is_tags_changed(old, new):
        old = set([o.strip() for o in old.split(',')])
        new = set([o.strip() for o in new.split(',')])
        return old == new

    def is_alias_changed(old, new):
        return old == new

    # 更新
    update_tables = []
    update_tables_cand = Table.objects.filter(pk__in=[schema['relation_name'] for schema in schemas])

    relationships_info = []
    for ut in update_tables_cand:
        schema = get_schema(ut.name)

        is_data_changed = False
        tags = ', '.join(schema.get('tags', []))
        alias = schema.get('alias', 'alias_' + str(uuid.uuid1())[:8])

        if is_tags_changed(ut.tags, tags):
            is_data_changed = True
            ut.tags = tags

        if is_alias_changed(ut.alias, alias):
            is_data_changed = True
            ut.alias = alias

        if is_data_changed:
            update_tables.append(ut)

        columns = set([column.name for column in ut.column_set.all()])

        add_columns_info = columns - set([column['name'] for column in schema['columns']])
        del_columns_info = set([column['name'] for column in schema['columns']]) - columns

        Column.objects.bulk_create([
            Column(
                table=ut,
                name=column['name'],
            )
            for column in add_columns_info
        ])
        Column.objects.filter(name__in=del_columns_info).delete()

        for column in schema['columns']:
            if column.get('foreign_key'):
                # Make sure the right table is in the same database with left table.
                right_table_name = '.'.join([ut.name.split('.')[0]] + column['foreign_key'].split('.'))
                relationship = Relationship.objects.filter(left_table_name=ut.name).filter(
                    right_table_name=right_table_name)
                if relationship:
                    for relation in relationship:
                        relation.join_type = column['join_type']
                        relation.join_condition = column['join_cond']
                        relation.save()
                else:
                    relationships_info.append({
                        'left_table_name': ut.name,
                        'right_table_name': right_table_name,
                        'join_type': column['join_type'],
                        'join_condition': column['join_cond'],
                    })

    Table.objects.bulk_update(update_tables, ['tags', 'alias'])

    # 新增
    add_schemas = [
        schema
        for schema in schemas
        if schema['relation_name'] not in [ut.name for ut in update_tables_cand]
    ]

    add_tables = []
    add_columns = []
    for schema in add_schemas:
        table = Table(
            urn=schema['relation_name'],
            name=schema['relation_name'],
            alias=schema.get('alias', 'alias_' + str(uuid.uuid1())[:8]),
            tags=', '.join(schema.get('tags', [])),
        )
        add_tables.append(table)

        for column in schema['columns']:
            add_columns.append(Column(
                table=table,
                name=column['name'],
            ))

            if column.get('foreign_key'):
                relationships_info.append({
                    'left_table_name': table.name,
                    'right_table_name': '.'.join([table.name.split('.')[0]] + column['foreign_key'].split('.')),
                    'join_type': column['join_type'],
                    'join_condition': column['join_cond'],
                })

    Table.objects.bulk_create(add_tables)
    Column.objects.bulk_create(add_columns)

    def get_table(relation_name):
        for ad in add_tables:
            if relation_name == ad.name:
                return ad

        for ut in update_tables_cand:
            if relation_name == ut.name:
                return ut

    relationships = []
    for relationship in relationships_info:
        left_table = get_table(relationship['left_table_name'])
        right_table = get_table(relationship['right_table_name'])
        relationships.append(Relationship(
            left_table_name=left_table,
            right_table_name=right_table,
            join_type=relationship['join_type'],
            join_condition=relationship['join_condition'],
        ))

    Relationship.objects.bulk_create(relationships)

    return HttpResponse()
