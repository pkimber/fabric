import os

from fabric.api import (
    abort,
    cd,
    env,
    get,
    local,
    prompt,
    put,
    run,
    sudo,
    task,
)
from fabric.colors import green
from fabric.colors import yellow
from fabric.contrib.files import exists

from lib.backup.path import Path
from lib.manage.command import DjangoCommand
from lib.server.folder import FolderInfo
from lib.site.info import SiteInfo


env.use_ssh_config = True
FILES = 'files'
POSTGRES = 'postgres'


def _local_database_exists(database_name):
    import psycopg2
    conn = psycopg2.connect('dbname={0} user={0}'.format('postgres'))
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pg_database WHERE datname='{}'".format(database_name))
    return cursor.fetchone()


def _local_postgres_user_exists(database_name):
    """ Return some data if the user exists, else 'None' """
    import psycopg2
    conn = psycopg2.connect('dbname={0} user={0}'.format('postgres'))
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pg_user WHERE usename = '{0}'".format(database_name))
    return cursor.fetchone()


@task
def backup_db(server_name, site_name):
    """ For docs, see https://github.com/pkimber/docs """
    print(green("Backup '{}' on '{}'").format(site_name, env.host_string))
    site_info = SiteInfo(server_name, site_name)
    db_type = 'postgres'
    if site_info.is_mysql():
        db_type = 'mysql'
    path = Path(site_name, db_type)
    run('mkdir -p {0}'.format(path.remote_folder()))
    if site_info.is_mysql():
        backup = site_info.backup()
        run('mysqldump --host={} --user={} --password={} {} > {}'.format(
            backup['host'],
            backup['user'],
            backup['pass'],
            backup['name'],
            path.remote_file(),
        ))
    else:
        run('pg_dump -U postgres {0} -f {1}'.format(
            site_name, path.remote_file()
        ))
    get(path.remote_file(), path.local_file())
    if site_info.is_mysql():
        pass
    else:
        print(green("restore to test database"))
        if _local_database_exists(path.test_database_name()):
            local('psql -X -U postgres -c "DROP DATABASE {0}"'.format(path.test_database_name()))
        local('psql -X -U postgres -c "CREATE DATABASE {0} TEMPLATE=template0 ENCODING=\'utf-8\';"'.format(path.test_database_name()))
        if not _local_postgres_user_exists(site_name):
            local('psql -X -U postgres -c "CREATE ROLE {0} WITH PASSWORD \'{1}\' NOSUPERUSER CREATEDB NOCREATEROLE LOGIN;"'.format(site_name, site_name))
        local("psql -X --set ON_ERROR_STOP=on -U postgres -d {0} --file {1}".format(
            path.test_database_name(), path.local_file()), capture=True
        )
        local('psql -X -U postgres -d {} -c "REASSIGN OWNED BY {} TO {}"'.format(
            path.test_database_name(), site_name, path.user_name()
        ))
        print(green("psql {}").format(path.test_database_name()))


@task
def backup_files():
    """
    To backup the files 'rs.connexionsw' server:
    fab -H rs.web.connexionsw backup_files
    """
    print(green("Backup files on '{}'").format(env.host_string))
    name = env.host_string.replace('.', '_')
    name = name.replace('-', '_')
    path = Path(name, 'files')
    run('mkdir -p {0}'.format(path.remote_folder()))
    with cd(path.files_folder()):
        run('tar -cvzf {} .'.format(path.remote_file()))
    get(path.remote_file(), path.local_file())


@task
def backup_php_site(server_name, site_name):
    site_info = SiteInfo(server_name, site_name)
    backup_path = site_info.backup().get('path')
    print(green("Backup files on '{}'").format(env.host_string))
    path = Path(site_name, 'files')
    print(yellow(path.remote_folder()))
    run('mkdir -p {0}'.format(path.remote_folder()))
    # remove '.gz' from end of tar file
    #  tar_file = os.path.splitext(path.remote_file())[0]
    #  with cd('/home/legalsec/legalsecretaryjournal.com/'):
    #      first = True
    #      for folder in path.php_folders():
    #          if first:
    #              first = False
    #              run('tar cvf {} {}'.format(tar_file, folder))
    #          else:
    #              run('tar rvf {} {}'.format(tar_file, folder))
    #  run('gzip {}'.format(tar_file))
    #  # list the contents of the archive
    #  run('tar ztvf {}'.format(path.remote_file()))
    with cd(backup_path):
        run('tar -cvzf {} .'.format(path.remote_file()))
    get(path.remote_file(), path.local_file())


@task
def create_db(server_name, site_name, table_space=None):
    """
    Note: table space 'cbs' is the name we have given to the Rackspace Cloud
    Block Storage volume.
    If you are not using cloud block storage, then don't use the
    ``table_space`` parameter.

    e.g.
    fab -H drop-temp create_db:prefix=pkimber,site_name=hatherleigh_net,table_space=

    # if your would like to specify a Postgres table space name
    fab -H drop-temp create_db:prefix=pkimber,site_name=hatherleigh_net,table_space=cbs

    psql parameters:
    -X  Do not read the start-up file
    """
    print(green("create '{}' database on '{}'").format(site_name, env.host_string))
    site_info = SiteInfo(server_name, site_name)
    if site_info.is_mysql():
        run('mysql -u root -e "CREATE USER \'{}\'@\'localhost\' IDENTIFIED BY \'{}\';"'.format(
            site_info.db_user(), site_info.password()
            )
        )
        run('mysql -u root -e "CREATE DATABASE {};"'.format(site_name))
        # I had loads of problems with this one.  bash evaluates back-ticks
        # first.  I think I solved the issue by adding 'shell=False' to 'run'.
        command = (
            "GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, "
            "ALTER, LOCK TABLES, CREATE TEMPORARY TABLES ON \`{}\`.* TO "
            "'{}'@'localhost' IDENTIFIED BY '{}';".format(
                site_name, site_info.db_user(), site_info.password()
            )
        )
        run('mysql -u root -e "{}"'.format(command), shell=False)
    else:
        #run('psql -X -U postgres -c "DROP DATABASE {};"'.format(site_name))
        run('psql -X -U postgres -c "CREATE ROLE {} WITH PASSWORD \'{}\' NOSUPERUSER CREATEDB NOCREATEROLE LOGIN;"'.format(
            site_name, site_info.password()
            ))
        parameter = ''
        if table_space:
            print(yellow("using block storage, table space {}...".format(table_space)))
            parameter = 'TABLESPACE={}'.format(table_space)
        run('psql -X -U postgres -c "CREATE DATABASE {} WITH OWNER={} TEMPLATE=template0 ENCODING=\'utf-8\' {};"'.format(
            site_name, site_name, parameter,
            ))
    print(green('done'))


@task
def db_version():
    """
    To find the Postgres version install on 'rs.db':
    fab -H rs.db db_version
    """
    print(green("Postgres version installed on '{0}'").format(env.host_string))
    run('psql -X -U postgres -c "SELECT VERSION();"')


@task
def haystack_index(prefix, name):
    """
    e.g:
    fab -H web@rs.web.connexionsw haystack_index:prefix=pkimber,name=csw_web
    """
    print(green("Haystack - reindex: '{}' on '{}' ").format(
        name, env.host_string)
    )
    site_info = SiteInfo(prefix, name)
    folder_info = FolderInfo(name)
    command = DjangoCommand(
        folder_info.live(),
        folder_info.live_venv(),
        site_info
    )
    command.haystack_index()


@task
def haystack_index_clear(prefix, name):
    """
    e.g:
    fab -H web@rs.web.connexionsw haystack_index:prefix=pkimber,name=csw_web
    """
    print(green("Haystack - reindex: '{}' on '{}' ").format(
        name, env.host_string)
    )
    confirm = ''
    while confirm not in ('Y', 'N'):
        confirm = prompt("Are you sure you want to clear the Haystack index (Y/N)?")
        confirm = confirm.strip().upper()
    if not confirm == 'Y':
        abort("exit")
    site_info = SiteInfo(prefix, name)
    folder_info = FolderInfo(name)
    command = DjangoCommand(
        folder_info.live(),
        folder_info.live_venv(),
        site_info
    )
    command.haystack_index_clear()


@task
def valid(server_name, site_name):
    """ For docs, see https://github.com/pkimber/docs """
    SiteInfo(server_name, site_name)
    print(green(
        "The configuration for '{}' appears to be valid"
        "").format(site_name)
    )


@task
def solr_status():
    print(green("SOLR status: '{0}'").format(env.host_string))
    #run('curl http://localhost:8080/solr/status/')
    run('curl http://localhost:8080/solr/')
    #run('psql -X -U postgres -c "SELECT VERSION();"')


@task
def ssl_cert(prefix, site_name):
    """
    fab -H server ssl_cert:prefix=pkimber,site_name=hatherleigh_net
    """
    site_info = SiteInfo(prefix, site_name)
    if not site_info.ssl():
        abort("'{}' is not set-up for SSL in the Salt pillar".format(site_name))
    folder_info = FolderInfo(site_name)
    if not exists(folder_info.srv_folder(), use_sudo=True):
        abort("{} folder does not exist on the server".format(folder_info.srv_folder()))
    if exists(folder_info.ssl_folder(), use_sudo=True):
        print(green("SSL folder exists: {}".format(folder_info.ssl_folder())))
    else:
        print(green("Create SSL folder: {}".format(folder_info.ssl_folder())))
        sudo('mkdir {}'.format(folder_info.ssl_folder()))
        sudo('chown www-data:www-data {}'.format(folder_info.ssl_folder()))
        sudo('chmod 0400 {}'.format(folder_info.ssl_folder()))
    if exists(folder_info.ssl_cert_folder(), use_sudo=True):
        print(green("Certificate folder exists: {}".format(folder_info.ssl_cert_folder())))
    else:
        print(green("Create certificate folder: {}".format(folder_info.ssl_cert_folder())))
        sudo('mkdir {}'.format(folder_info.ssl_cert_folder()))
        sudo('chown www-data:www-data {}'.format(folder_info.ssl_cert_folder()))
        sudo('chmod 0400 {}'.format(folder_info.ssl_cert_folder()))
    put(
        site_info.ssl_cert(),
        folder_info.ssl_cert(),
        use_sudo=True,
        mode=0400,
    )
    sudo('chown www-data:www-data {}'.format(folder_info.ssl_cert()))
    print(green(folder_info.ssl_cert()))
    put(
        site_info.ssl_server_key(),
        folder_info.ssl_server_key(),
        use_sudo=True,
        mode=0400,
    )
    sudo('chown www-data:www-data {}'.format(folder_info.ssl_server_key()))
    print(green(folder_info.ssl_server_key()))
    print(yellow("Complete"))
