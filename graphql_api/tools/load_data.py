import sqlite3
import uuid

from dbutils import connection

if __name__ == '__main__':
    tables = []
    aliases = []
    with connection(prod=False) as conn:
        with conn.cursor() as cursor:
            cursor.execute('set search_path to dwd, dim')
            cursor.execute(f"select distinct tablename from pg_table_def where schemaname = 'dim'")
            for row in cursor.fetchall():
                table_name = row[0]
                table_alias = ''.join([word[0] for word in table_name.split('_')])
                tables.append([table_name, table_alias, 'dim'])
                aliases.append(table_alias)

            cursor.execute(f"select distinct tablename from pg_table_def where schemaname = 'dwd'")
            for row in cursor.fetchall():
                table_name = row[0]
                table_alias = ''.join([word[0] for word in table_name.split('_')])
                tables.append([table_name, table_alias, 'dwd'])
                aliases.append(table_alias)

    for i in range(len(tables)):
        if aliases.count(tables[i][1]) > 1:
            tables[i][1] = f'{tables[i][1]}_{str(uuid.uuid1())[:8]}'

    for table in tables:
        table_name = table[0]
        table_alias = table[1]
        table_type = table[2].upper()

        with connection(prod=False) as conn:
            with conn.cursor() as cursor:
                cursor.execute('set search_path to dwd, dim')
                cursor.execute(f'''
                    SELECT * FROM pg_table_def WHERE tablename = '{table_name}';
                ''')

                columns = [row[2] for row in cursor.fetchall()]

                with sqlite3.connect('../../db.sqlite3') as rs_conn:
                    is_table_exist = False
                    rs_cursor = rs_conn.cursor()
                    sql = f"select name from graphql_api_table where name = '{table_name}'"
                    rs_cursor.execute(sql)
                    if rs_cursor.fetchone():
                        continue

                    sql = f"insert into graphql_api_table (name, alias, table_type) values ('{table_name}', '{table_alias}', '{table_type}')"
                    rs_cursor.execute(sql)

                    sql = f"select id from graphql_api_table where name = '{table_name}'"
                    rs_cursor.execute(sql)
                    table_id = rs_cursor.fetchone()[0]

                    for column in columns:
                        sql = f"insert into graphql_api_column (name, table_id) values ('{column}', {table_id})"
                        rs_cursor.execute(sql)
