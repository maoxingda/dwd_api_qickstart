import os

import graphene
from jinja2 import Template

from graphql_api.models import Table, Relationship
from graphql_api.tools.dbutils import connection
from graphql_api.tools.parser import parse


def resolve_func(cls, context):
    tables = Table.objects.all()
    tables_alias = {table.name.split('.')[-1]: table.alias for table in tables}

    def get_table(table_name_):
        for table in tables:
            if table.name.split('.')[-1] == table_name_:
                return table

    # parse from tables and select columns from graphql context
    from_tables = parse(context.field_asts, tables_alias)

    if not from_tables:
        return

    # cat sql
    table_name = ''
    from_clause = []
    select_columns = []
    for table_name, value in from_tables.items():
        table = get_table(table_name)
        parent_table = get_table(value['parent'])
        select_columns += [f'{column} as {column.replace(".", "_")}' if len(from_tables.keys()) > 1 else column for
                           column in value['columns']]

        if not parent_table:
            continue

        # query relationship from db
        relationships = Relationship.objects.filter(
            left_table_name__name=parent_table.name).filter(right_table_name__name=table.name)

        # WARN: make sure that：len(relationships) == 1
        assert len(relationships) == 1, f'({parent_table.name} ---> {table.name}), relationship not unique.'

        for relationship in relationships:
            table_fq = table.name
            parent_table_fq = parent_table.name

            if f'{parent_table_fq} as {parent_table.alias}' not in from_clause:
                from_clause.append(f'{parent_table_fq} as {parent_table.alias}')

            from_clause.append(relationship.join_type.lower().replace("_", " "))

            if f'{table_fq} as {table.alias}' not in from_clause:
                from_clause.append(f'{table_fq} as {table.alias}')

            from_clause.append('on')

            from_clause.append(
                Template(relationship.join_condition).render({'l': parent_table.alias, 'r': table.alias}))

    sql = [
        f'select {", ".join(select_columns if from_clause else [column.split(".")[-1] for column in select_columns])}',
        f'from {" ".join(from_clause if from_clause else [get_table(table_name).name])}'
    ]

    # test only.
    is_execute_sql = any(['data' == field.name.value for field in context.field_asts[0].selection_set.selections])
    if is_execute_sql:
        with connection(prod=os.environ.get('prod', '0')) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f'select * from ({" ".join(sql)}) limit 1')
                data = cursor.fetchone()
                if data:
                    return cls(sql=' '.join(sql), data=", ".join([str(d) for d in data]))

    return cls(sql=' '.join(sql))


class MeicanObjectType(graphene.ObjectType):
    sql = graphene.String()
    data = graphene.String(description='test only.')
