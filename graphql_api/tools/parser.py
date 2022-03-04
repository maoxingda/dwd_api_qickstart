"""Parse tables and select columns list from graphql AST"""


def parse(ast, tables):
    def get_table_alias(table_name):
        for table in tables:
            if table_name == table.name:
                return table.alias

    def _parse(node, tables, table_name, level):
        if level > 2:
            tables[node.name.value] = {
                'columns': [],
                'parent': table_name
            }

        for field in node.selection_set.selections:
            if level == 2 and field.name.value in ('sql', 'data'):
                continue
            if field.selection_set is None:
                tables[node.name.value]['columns'].append(f'{get_table_alias(node.name.value)}.{field.name.value}')
                continue

            _parse(field, tables, node.name.value, level + 1)

        return tables

    return _parse(ast[0], {}, '', 2)
