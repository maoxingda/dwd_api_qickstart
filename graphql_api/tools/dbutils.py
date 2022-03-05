import os

import psycopg2


def connection(prod):
    if prod == '1':
        return psycopg2.connect(os.environ['proddbaddr'])

    return psycopg2.connect(os.environ['sandboxdbaddr'])
