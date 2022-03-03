import logging

import graphene

from jinja2 import Template

from graphql_api.constants.constant import TableTypes
from graphql_api.models import Table
from graphene.utils.str_converters import to_camel_case, to_snake_case

logger = logging.getLogger(__name__)


def build_schema():
    logger.info("Building schema...")
    tables = []
    for table in Table.objects.all():
        table_columns = [str(column) for column in table.column_set.all()]

        relationships = []
        if table.table_type == TableTypes.DWD.name:
            relationships1 = [relation for relation in table.left_table_name.all() if relation.left_table_name_id == table.id]
            relationships2 = [relation for relation in table.right_table_name.all() if relation.right_table_name_id == table.id]
            relationships = relationships1 + relationships2

        relationships_content = []
        for relation in relationships:
            relation_table_name = relation.right_table_name.name[0].upper() + to_camel_case(relation.right_table_name.name[1:])
            relation_field_name = to_snake_case(relation.right_table_name.name)
            relationships_content.append({
                'relation_table_name': relation_table_name,
                'relation_field_name': relation_field_name,
            })

        tables.append({
            'table_name': table.name[0].upper() + to_camel_case(table.name[1:]),
            'field_name': table.name,
            'table_type': table.table_type,
            'table_columns': table_columns,
            'relationships': relationships_content,
        })

    with open('graphql_api/tools/schema_template.jinja2') as f:
        content = Template(f.read()).render({'tables': tables})

    with open('graphql_api/schema.py', 'w') as f:
        f.write(content)

    logger.info("Build schema finished.")

    from graphql_api.schema import Query

    return graphene.Schema(query=Query, auto_camelcase=False)  # type: ignore
