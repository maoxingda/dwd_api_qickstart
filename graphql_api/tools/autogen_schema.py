import logging
import os
from datetime import datetime

import graphene
from graphene.utils.str_converters import to_camel_case, to_snake_case
from jinja2 import Template

from graphql_api.models import Table, Relationship

logger = logging.getLogger(__name__)


def build_schema():
    if os.environ.get('rebuild_schema', '0') == '1':
        logger.info("Building schema...")

        start = datetime.utcnow()

        tables = Table.objects.all()
        relationships = Relationship.objects.all()

        # Collect table's directly children.
        tables_children = {}
        table_types = {}
        for table in tables:
            table_types[table.name] = table.table_type
            tables_children[table.name] = []
            for relationship in relationships:
                if relationship.left_table_name_id == table.id:
                    tables_children[table.name].append(relationship.right_table_name.name)

        def sort_tables(tables, tables_visited):
            def is_visited(table, tables_visited):
                tables = []
                for tv in tables_visited:
                    tables += tv.keys()
                return table in tables

            for table, table_children in tables.items():
                if any(table in tv.keys() for tv in tables_visited):
                    continue
                elif len(table_children) == 0 or all(is_visited(child, tables_visited) for child in table_children):
                    tables_visited.append({table: table_children})
                    tables[table] = None
            if any(table_children for _, table_children in tables.items()):
                return sort_tables(tables, tables_visited)
            else:
                return tables_visited

        # define leaf node firstly.
        tables_children = sort_tables(tables_children, [])

        # prepare template substitution context.
        graphql_objects = []
        for table in tables_children:
            for table_name, children in table.items():
                table_columns = [str(column) for t in tables for column in t.column_set.all() if t.name == table_name]

                # skip empty table
                if len(table_columns) == 0:
                    break

                table_children = []
                for child in children:
                    child_table_name = child[0].upper() + to_camel_case(child[1:])
                    child_field_name = to_snake_case(child)
                    table_children.append({
                        'child_table_name': child_table_name,
                        'child_field_name': child_field_name,
                    })

                graphql_objects.append({
                    'class_name': table_name[0].upper() + to_camel_case(table_name[1:]),
                    'wrapper_class_field_name': table_name,
                    'table_type': table_types[table_name],
                    'fields': table_columns,
                    'children': table_children,
                })

        with open('graphql_api/tools/schema_template.jinja2') as f:
            template_code = Template(f.read()).render({'objects': graphql_objects})

        with open('graphql_api/schema.py', 'w') as f:
            f.write(template_code)

        end = datetime.utcnow()

        if (end - start).seconds < 60:
            logger.info(f'Elapsed: {(end - start).seconds} seconds.')
        else:
            logger.info(f'Elapsed: {(end - start).seconds / 60} minutes.')

        logger.info("Build schema finished.")

    from graphql_api.schema import Query

    return graphene.Schema(query=Query, auto_camelcase=False)  # type: ignore
