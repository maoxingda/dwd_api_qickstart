import logging
import os
import time

import graphene
from django.conf import settings
from django.core.exceptions import ValidationError
from graphene.utils.str_converters import to_camel_case, to_snake_case
from jinja2 import Template

from graphql_api.models import Table, Relationship

logger = logging.getLogger(__name__)


def dfs(vertices, vertices_visited, validate=False):
    keys_visited_len = len(vertices_visited.keys())

    for vetex, child_vetxcies in vertices.items():
        if vetex in vertices_visited.keys():
            continue
        elif not child_vetxcies or all(child_vetex in vertices_visited.keys() for child_vetex in child_vetxcies):
            vertices_visited[vetex] = child_vetxcies

    if validate and keys_visited_len == len(vertices_visited.keys()):
        raise ValidationError(f'DAG exist circle...')

    if vertices != vertices_visited:
        return dfs(vertices, vertices_visited)

    return vertices_visited


def build_schema():
    if os.environ.get('rebuild_schema', '0') == '1':
        start = time.time()

        logger.info("Building schema...")

        tables = Table.objects.all()
        relationships = Relationship.objects.all()

        # collect table's children.
        is_query_entry = {}
        tables_children = {}
        for table in tables:
            is_query_entry[table.name] = settings.DWD_API_TAGS['entry'] in table.tags.split(',')
            tables_children[table.name] = []
            for relationship in relationships:
                if relationship.left_table_name_id == table.pk:
                    tables_children[table.name].append(relationship.right_table_name.name)

        # define leaf node firstly.
        tables_children = dfs(tables_children, {})

        # prepare template substitution context.
        graphql_objects = []
        for table_name, children in tables_children.items():
            table_columns = [
                column.name for table in tables for column in table.column_set.all()
                if table.name == table_name
            ]

            # skip empty table
            if not table_columns:
                break

            table_children = []
            for child in children:
                child_table_name = child.split('.')[-1][0].upper() + to_camel_case(child.split('.')[-1][1:])
                child_field_name = to_snake_case(child.split('.')[-1])
                table_children.append({
                    'child_table_name': child_table_name,
                    'child_field_name': child_field_name,
                })

            graphql_objects.append({
                'class_name': table_name.split('.')[-1][0].upper() + to_camel_case(table_name.split('.')[-1][1:]),
                'wrapper_class_field_name': table_name.split('.')[-1],
                'entry': is_query_entry[table_name],
                'fields': table_columns,
                'children': table_children,
            })

        with open('graphql_api/tools/schema_template.jinja2') as f:
            template_code = Template(f.read()).render({'objects': graphql_objects})

        with open('graphql_api/schema.py', 'w') as f:
            f.write(template_code)

        logger.info("Build schema finished.")

        end = time.time()

        if end - start < 60:
            logger.info(f'Elapsed: {int(end - start)} seconds.')
        else:
            logger.info(f'Elapsed: {(end - start) // 60} minutes.')

    from graphql_api.schema import Query

    return graphene.Schema(query=Query, auto_camelcase=False)  # type: ignore
