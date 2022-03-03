"""Parse tables and select columns list from graphql AST"""


def parse(ast):
    def _parse(node, tables, table_name):
        if node.name.value == 'sql':
            return
        if node.selection_set is None:
            tables[table_name].append(node.name.value)
            return
        if not node.name.value.endswith('_with_sql'):
            tables[node.name.value] = []
        for field in node.selection_set.selections:
            _parse(field, tables, node.name.value)
        return tables

    return _parse(ast[0], {}, '')
