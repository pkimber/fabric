# -*- encoding: utf-8 -*-

from fabric.api import (
    local,
    run,
)
from fabric.context_managers import shell_env

from lib.error import TaskError


def _db_host(site_info):
    result = ''
    if site_info.db_host:
        result = ' --host={} '.format(site_info.db_host)
    return result


def _pg_data_database(site_info):
    result = {}
    if site_info.db_pass:
        result.update(dict(PGPASSWORD=site_info.db_pass))
    return result


def _pg_data_postgres(site_info):
    result = {}
    if site_info.postgres_pass:
        result.update(dict(PGPASSWORD=site_info.postgres_pass))
    return result


def _result_true_or_false(out):
    result = False
    if int(out) == 1:
        result = True
    elif int(out) == 0:
        result = False
    else:
        message = "Cannot work out if 'local_database_exists': {}".format(out)
        raise TaskError(message)
    return result


def _sql_user_create(user_name, password):
    return (
        "CREATE ROLE {} WITH PASSWORD '{}' "
        "NOSUPERUSER CREATEDB NOCREATEROLE LOGIN".format(user_name, password)
    )


def _sql_database_create(database_name, table_space):
    parameter = ''
    if table_space:
        print(yellow("using block storage - table space: {}".format(table_space)))
        parameter = 'TABLESPACE={}'.format(table_space)
    return (
        "CREATE DATABASE {} "
        "TEMPLATE=template0 ENCODING='utf-8' {};".format(database_name, parameter)
    )


def _sql_database_exists(database_name):
    return "SELECT COUNT(*) FROM pg_database WHERE datname='{}'".format(
        database_name
    )


def _sql_database_owner(database_name, user_name):
    return "ALTER DATABASE {} OWNER TO {}".format(database_name, user_name)


def _sql_drop_database(database_name):
    return "DROP DATABASE {}".format(database_name)


def _sql_drop_user(user_name):
    return "DROP ROLE {}".format(user_name)


def _sql_reassign_owner(from_user_name, to_user_name):
    return "REASSIGN OWNED BY {} TO {}".format(from_user_name, to_user_name)


def _sql_user_exists(user_name):
    return "SELECT COUNT(*) FROM pg_user WHERE usename = '{}'".format(
        user_name
    )


def _run_local(sql, database_name=None):
    database = ''
    if database_name:
        database = '-d {}'.format(database_name)
    local('psql -X -U postgres {} -c "{}"'.format(database, sql))


def _run_local_psycopg2(sql):
    import psycopg2
    conn = psycopg2.connect('dbname={0} user={0}'.format('postgres'))
    cursor = conn.cursor()
    cursor.execute(sql)
    return cursor.fetchone()


def _run_remote(site_info, sql):
    """Run a remote command as the 'postgres' user.

    We need the 'postgres' user to create a role or database.
    """
    pg_data = _pg_data_postgres(site_info)
    with shell_env(**pg_data):
        result = run('psql -X {} -U postgres -t -A -c "{}"'.format(
            _db_host(site_info),
            sql,
        ))
    return result


def _run_remote_as_user(site_info, sql):
    """Run a remote command as the user of the database.

    We need to log into the database as the owner to delete the database.
    """
    pg_data = _pg_data_database(site_info)
    with shell_env(**pg_data):
        result = run('psql -X {} -U {} -d postgres -t -A -c "{}"'.format(
            _db_host(site_info),
            site_info.site_name,
            sql,
        ))
    return result


def drop_local_database(database_name):
    sql = _sql_drop_database(database_name)
    _run_local(sql)


def drop_remote_database(site_info):
    sql = _sql_drop_database(site_info.db_name)
    _run_remote_as_user(site_info, sql)


def drop_remote_user(site_info):
    sql = _sql_drop_user(site_info.site_name)
    _run_remote(site_info, sql)


def local_database_create(database_name):
    sql = _sql_database_create(database_name, None)
    _run_local(sql)


def local_database_exists(database_name):
    sql = _sql_database_exists(database_name)
    result = _run_local_psycopg2(sql)
    return _result_true_or_false(result[0])


def local_load_file(database_name, file_name):
    local(
        "psql -X --set ON_ERROR_STOP=on -U postgres -d {0} --file {1}".format(
            database_name,
            file_name,
        ),
        capture=True,
    )


def local_reassign_owner(database_name, from_user_name, to_user_name):
    sql = _sql_reassign_owner(from_user_name, to_user_name)
    _run_local(sql, database_name)


def local_user_create(site_info):
    sql = _sql_user_create(site_info.site_name, site_info.site_name)
    _run_local(sql)


def local_user_exists(site_info):
    sql = _sql_user_exists(site_info.site_name)
    result = _run_local_psycopg2(sql)
    return _result_true_or_false(result[0])


def remote_database_create(site_info, table_space):
    sql = _sql_database_create(site_info.db_name, table_space)
    _run_remote(site_info, sql)
    # amazon rds the 'postgres' user sets the owner (after the database is created)
    sql = _sql_database_owner(site_info.db_name, site_info.site_name)
    _run_remote(site_info, sql)


def remote_database_exists(site_info):
    sql = _sql_database_exists(site_info.db_name)
    result = _run_remote(site_info, sql)
    return _result_true_or_false(result)


def remote_user_create(site_info):
    sql = _sql_user_create(site_info.site_name, site_info.db_pass)
    _run_remote(site_info, sql)


def remote_user_exists(site_info):
    sql = _sql_user_exists(site_info.site_name)
    result = _run_remote(site_info, sql)
    return _result_true_or_false(result)
