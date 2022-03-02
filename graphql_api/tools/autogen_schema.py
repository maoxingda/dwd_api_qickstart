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
        class_name = table.name[0].upper() + to_camel_case(table.name[1:])
        relationships = []
        if table.table_type == 'dwd':
            relationships1 = [relation for relation in table.left_table_name.all() if relation.left_table_name_id == table.id]
            relationships2 = [relation for relation in table.right_table_name.all() if relation.right_table_name_id == table.id]
            relationships = relationships1 + relationships2
        columns = []
        for column in table.column_set.all():
            columns.append(str(column))
        relationships_content = []
        for relation in relationships:
            relation_class_name = relation.right_table_name.name[0].upper() + to_camel_case(relation.right_table_name.name[1:])
            relation_field_name = to_camel_case(relation.right_table_name.name)
            relationships_content.append({
                'relation_class_name': relation_class_name,
                'relation_field_name': relation_field_name,
            })
        code_objs.append({
            'class_name': class_name,
            'field_name': table.name,
            'table_type': table.table_type,
            'columns': columns,
            'relationships': relationships_content,
        })

    content = Template(open('graphql_api/tools/schema_template.jinja2').read()).render({
        'codes': code_objs,
    })

    with open('graphql_api/schema.py', 'w') as f:
        f.write(content)

    logger.info("Build schema finished.")

    from graphql_api.schema import Query

    return graphene.Schema(query=Query)  # type: ignore
