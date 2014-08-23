from fabric.api import (
    abort,
    cd,
    env,
    get,
    hide,
    local,
    prompt,
    put,
    run,
    sudo,
    task,
)
from fabric.colors import (
    cyan,
    green,
    yellow,
)
from fabric.contrib.files import exists

from lib.backup.path import Path
from lib.deploy.helper import (
    deploy_django,
    deploy_php,
    django_post_deploy,
    link_install_to_live_folder,
    run_post_deploy_test,
)
from lib.dev.folder import get_pillar_folder
from lib.manage.command import DjangoCommand
from lib.server.folder import FolderInfo
from lib.server.name import get_server_name_live
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


def backup_database(server_name, site_name):
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
        run('whoami')
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
def backup_db():
    """For docs, see https://github.com/pkimber/docs"""
    print(green("Backup '{}' on '{}'").format(env.site_name, env.hosts))
    backup_database(env.hosts, env.site_name)


@task
def backup_db_deprecated(server_name, site_name):
    """For old PHP servers on Dreamhost."""
    backup_database(server_name, site_name)


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
    with cd(path.files_folder()), hide('stdout'):
        run('tar -cvzf {} .'.format(path.remote_file()))
    get(path.remote_file(), path.local_file())


@task
def backup_ftp():
    site_info = SiteInfo(env.hosts, env.site_name)
    if not site_info.is_ftp():
        abort("'{}' is not set-up for 'ftp'".format(env.site_name))
    print(green("Backup FTP files on '{}'").format(env.host_string))
    path = Path(env.site_name, 'ftp')
    run('mkdir -p {0}'.format(path.remote_folder()))
    with cd(path.ftp_folder(env.site_name)):
        run('tar -cvzf {} .'.format(path.remote_file()))
    get(path.remote_file(), path.local_file())


@task
def backup_php_site(server_name, site_name):
    """

    legalsecretaryjournal_com
    TODO Only really need to backup everything in the 'images' and 'sites'
    folder.
    """
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
def create_db(table_space=None):
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
    print(green("create '{}' database on '{}'").format(env.site_name, env.host_string))
    site_info = SiteInfo(env.hosts, env.site_name)
    if site_info.is_mysql():
        # TODO
        # Note: these commands will not work if the root user has a password!
        # For more information, see:
        # Securing the Initial MySQL Accounts:
        # http://docs.oracle.com/cd/E17952_01/refman-5.1-en/default-privileges.html
        # Setting mysql root password the first time:
        # https://github.com/saltstack/salt/issues/5918
        # I have a task on my list to set the password automatically
        run('mysql -u root -e "CREATE USER \'{}\'@\'localhost\' IDENTIFIED BY \'{}\';"'.format(
            site_info.db_user(), site_info.password()
            )
        )
        run('mysql -u root -e "CREATE DATABASE {};"'.format(env.site_name))
        # I had loads of problems with this one.  bash evaluates back-ticks
        # first.  I think I solved the issue by adding 'shell=False' to 'run'.
        command = (
            "GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, "
            "ALTER, LOCK TABLES, CREATE TEMPORARY TABLES ON \`{}\`.* TO "
            "'{}'@'localhost' IDENTIFIED BY '{}';".format(
                env.site_name, site_info.db_user(), site_info.password()
            )
        )
        run('mysql -u root -e "{}"'.format(command), shell=False)
    else:
        #run('psql -X -U postgres -c "DROP DATABASE {};"'.format(env.site_name))
        run('psql -X -U postgres -c "CREATE ROLE {} WITH PASSWORD \'{}\' NOSUPERUSER CREATEDB NOCREATEROLE LOGIN;"'.format(
            env.site_name, site_info.password()
            ))
        parameter = ''
        if table_space:
            print(yellow("using block storage, table space {}...".format(table_space)))
            parameter = 'TABLESPACE={}'.format(table_space)
        run('psql -X -U postgres -c "CREATE DATABASE {} WITH OWNER={} TEMPLATE=template0 ENCODING=\'utf-8\' {};"'.format(
            env.site_name, env.site_name, parameter,
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
def deploy(version):
    """ For docs, see https://github.com/pkimber/cloud_docs """
    env.user = 'web'
    site_info = SiteInfo(env.hosts, env.site_name)
    folder_info = FolderInfo(env.site_name, version)
    # validate
    if exists(folder_info.install()):
        raise Exception(
            'Install folder {} already exists'.format(folder_info.install())
        )
    print(green(folder_info.install()))
    # create folders
    if not exists(folder_info.deploy()):
        run('mkdir {}'.format(folder_info.deploy()))
    run('mkdir {}'.format(folder_info.install()))
    run('mkdir {}'.format(folder_info.install_temp()))
    if site_info.is_php():
        deploy_php(folder_info, site_info)
    else:
        deploy_django(folder_info, site_info, version)
    # symbolic link
    link_install_to_live_folder(folder_info.install(), folder_info.live())
    if site_info.is_django():
        django_post_deploy(folder_info)
    # Post deploy
    run_post_deploy_test(env.site_name)


@task
def haystack_index():
    """ For docs, see https://github.com/pkimber/cloud_docs """
    env.user = 'web'
    print(green("Haystack - reindex: '{}' on '{}' ").format(
        env.site_name, env.hosts)
    )
    site_info = SiteInfo(env.hosts, env.site_name)
    folder_info = FolderInfo(env.site_name)
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
def ok(site_name):
    """
    Test a live site (automatically done at the end of a deploy)

    e.g:
    fab -f deploy.py ok:name=csw_web
    """
    run_post_deploy_test(site_name)


@task
def site(site_name):
    print(green("site_name: {}".format(site_name)))
    # find the server name for this site
    pillar_folder = get_pillar_folder()
    print(green("pillar: {}".format(pillar_folder)))
    server_name = get_server_name_live(pillar_folder, site_name)
    print(yellow("server_name: {}".format(server_name)))
    # Update env.hosts instead of calling execute()
    env.hosts = server_name
    env.site_name = site_name


@task
def version():
    print(yellow(env.site_name))
    run('uname -r')

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
def ssl_cert():
    """ For docs, see https://github.com/pkimber/docs."""
    site_info = SiteInfo(env.hosts, env.site_name)
    if not site_info.ssl():
        abort("'{}' is not set-up for SSL in the Salt pillar".format(env.site_name))
    folder_info = FolderInfo(env.site_name)
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
