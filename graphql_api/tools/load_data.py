import sqlite3
import uuid
import time

from dbutils import connection

if __name__ == '__main__':
    prod = '1'
    tables = []
    aliases = []
    start = time.time()

    with connection(prod=prod) as get_tables_conn:
        with get_tables_conn.cursor() as get_tables_cursor:
            get_tables_cursor.execute('set search_path to dwd, dim')
            get_tables_cursor.execute(f"select distinct tablename from pg_table_def where schemaname = 'dim'")

            for row in get_tables_cursor.fetchall():
                table_name = row[0]
                table_alias = ''.join([word[0] for word in table_name.split('_')])
                tables.append([table_name, table_alias, 'dim'])
                aliases.append(table_alias)

            get_tables_cursor.execute(f"select distinct tablename from pg_table_def where schemaname = 'dwd'")
            for row in get_tables_cursor.fetchall():
                table_name = row[0]
                table_alias = ''.join([word[0] for word in table_name.split('_')])
                tables.append([table_name, table_alias, 'dwd'])
                aliases.append(table_alias)

    for i in range(len(tables)):
        if aliases.count(tables[i][1]) > 1:
            tables[i][1] = f'{tables[i][1]}_{str(uuid.uuid1())[:8]}'

    with sqlite3.connect('../../db.sqlite3') as truncate_conn:
        truncate_cursor = truncate_conn.cursor()
        sql = "delete from graphql_api_column"
        truncate_cursor.execute(sql)
        sql = "delete from graphql_api_relationship"
        truncate_cursor.execute(sql)
        sql = "delete from graphql_api_table"
        truncate_cursor.execute(sql)

    table_column_ref = []
    with connection(prod=prod) as get_table_columns_conn:
        with get_table_columns_conn.cursor() as get_table_columns_cursor:
            with sqlite3.connect('../../db.sqlite3') as sqlite_conn:
                sqlite_cursor = sqlite_conn.cursor()
                for table in tables:
                    table_name = table[0]
                    table_alias = table[1]
                    table_type = table[2].upper()

                    # if table_name not in ('user_orders', 'meal_plans', 'cities'):
                    #     continue

                    get_table_columns_cursor.execute('set search_path to dwd, dim')
                    get_table_columns_cursor.execute(f'''
                        select * from pg_table_def where tablename = '{table_name}';
                    ''')

                    # sql = f"select name from graphql_api_table where name = '{table_name}'"
                    # sqlite_cursor.execute(sql)
                    # if sqlite_cursor.fetchone():
                    #     continue

                    sql = f"insert into graphql_api_table (name, alias, table_type) values ('{table_name}', '{table_alias}', '{table_type}')"
                    sqlite_cursor.execute(sql)
                    print(sql)

                    sql = f"select id from graphql_api_table where name = '{table_name}'"
                    sqlite_cursor.execute(sql)

                    table_id = sqlite_cursor.fetchone()[0]

                    for column in [row[2] for row in get_table_columns_cursor.fetchall()]:
                        sql = f"insert into graphql_api_column (name, table_id) values ('{column}', {table_id})"
                        sqlite_cursor.execute(sql)
                        print(sql)

                        if column.endswith('_id'):
                            ref_table_name = column[:-3]
                            if any([ref_table_name == t[0] and ref_table_name != table_name for t in tables]):
                                table_column_ref.append([table_id, table_name, table_alias, column, ref_table_name])
                            ref_table_name += 's'
                            if any([ref_table_name == t[0] and ref_table_name != table_name for t in tables]):
                                table_column_ref.append([table_id, table_name, table_alias, column, ref_table_name])

    with sqlite3.connect('../../db.sqlite3') as insert_relationship_conn:
        insert_relationship_sqlite_cursor = insert_relationship_conn.cursor()
        for ref in table_column_ref:
            ltbl_id = ref[0]
            ltbl_alias = ref[2]
            ref_col = ref[3]
            ref_table_name = ref[4]

            sql = f"select id, alias from graphql_api_table where name = '{ref_table_name}'"
            insert_relationship_sqlite_cursor.execute(sql)
            row = insert_relationship_sqlite_cursor.fetchone()
            ref_table_id = row[0]
            ref_table_alias = row[1]

            sql = f"""
                insert into graphql_api_relationship (left_table_name_id, right_table_name_id, join_type, join_condition) 
                values ('{ltbl_id}', '{ref_table_id}', 'INNER_JOIN', '{{{{ l }}}}.{ref_col} = {{{{ r }}}}.id')
            """
            insert_relationship_sqlite_cursor.execute(sql)
            print(sql)

    end = time.time()

    if end - start < 60:
        print(f'Elapsed: {int(end - start)} seconds.')
    else:
        print(f'Elapsed: {(end - start) // 60} minutes.')
