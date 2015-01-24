# -*- encoding: utf-8 -*-


def local_database_exists(database_name):
    import psycopg2
    conn = psycopg2.connect('dbname={0} user={0}'.format('postgres'))
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pg_database WHERE datname='{}'".format(database_name))
    return cursor.fetchone()


def local_postgres_user_exists(database_name):
    """ Return some data if the user exists, else 'None' """
    import psycopg2
    conn = psycopg2.connect('dbname={0} user={0}'.format('postgres'))
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pg_user WHERE usename = '{0}'".format(database_name))
    return cursor.fetchone()
