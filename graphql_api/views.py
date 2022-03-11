from string import Template

from django.http import HttpResponse
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

from graphql_api.models import Table, Column


def update_schema(request):
    transport = RequestsHTTPTransport(
        url='http://localhost:8080/api/graphql/',  # FIXME
        headers={'X-DataHub-Actor': 'urn:li:corpuser:datahub'})

    client = Client(transport=transport)

    query = '''
        {
          search(input: {type: DATASET, query: "business-procedure", start: $start, count: 1}) {
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
        query_sub = Template(query).safe_substitute(start=start)

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

    add_columns = []
    for ut in update_tables:
        schema = get_schema(ut.urn)
        ut.tags = ', '.join([tag.split(':')[-1] for tag in schema[2]])

        ut.column_set.all().delete()

        for column in schema[3]:
            add_columns.append(Column(
                table=ut,
                name=column
            ))

    Table.objects.bulk_update(update_tables)
    Column.objects.bulk_create(add_columns)

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
            name=schema[1].split('.')[-1],
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

    return HttpResponse(status=200)
