import os

import psycopg2


def connection(prod=None):
    if prod:
        return psycopg2.connect(os.environ['proddbaddr'])

    return psycopg2.connect(os.environ['sandboxdbaddr'])
