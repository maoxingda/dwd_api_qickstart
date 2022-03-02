import logging
from pprint import pprint

import graphene

from jinja2 import Template
from graphql_api.models import Table
from graphene.utils.str_converters import to_camel_case

logger = logging.getLogger(__name__)


def build_schema():
    logger.info("Building schema...")
    code_objs = []
    for table in Table.objects.all():
        table_name = table.name[0].upper() + to_camel_case(table.name[1:])
        relationships1 = [relation for relation in table.left_table_name.all() if relation.left_table_name_id == table.id]
        relationships2 = [relation for relation in table.right_table_name.all() if relation.right_table_name_id == table.id]
        relationships = relationships1 + relationships2
        for relation in relationships:
            print(relation.left_table_name)
        columns = []
        for column in table.column_set.all():
            columns.append(str(column))
        code_objs.append({
            'table_name': table_name,
            'table_type': table.table_type,
            'columns': columns,
            'relationships': [
                to_camel_case(relation.right_table_name.name) for relation in relationships
            ]
        })

    content = Template(open('graphql_api/tools/schema_template.jinja2').read()).render({
        'codes': code_objs
    })

    pprint(code_objs)

    with open('graphql_api/schema.py', 'w') as f:
        f.write(content)
        f.write('\n')

    logger.info("Build schema finished.")

    from graphql_api.schema import Query

    return graphene.Schema(query=Query)  # type: ignore
