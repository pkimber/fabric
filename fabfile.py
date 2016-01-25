# -*- encoding: utf-8 -*-
from datetime import datetime

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
    red,
    yellow,
)
from fabric.context_managers import shell_env
from fabric.contrib.files import exists

from lib.path import Path
from lib.deploy import (
    deploy_django,
    deploy_php,
    django_post_deploy,
    link_install_to_live_folder,
    run_post_deploy_test,
)
from lib.folder import get_pillar_folder
from lib.duplicity import Duplicity
from lib.command import DjangoCommand
from lib.postgres import (
    drop_remote_database,
    drop_remote_user,
    local_database_exists,
    local_user_exists,
    remote_database_create,
    remote_database_exists,
    remote_user_create,
    remote_user_exists,
)
from lib.folder import FolderInfo
from lib.server import get_server_name
from lib.siteinfo import SiteInfo


FILES = 'files'
POSTGRES = 'postgres'
env.use_ssh_config = False


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
        run('tar -czf {} .'.format(path.remote_file()))
    get(path.remote_file(), path.local_file())


@task
def backup_ftp():
    if not env.site_info.is_ftp():
        abort("'{}' is not set-up for 'ftp'".format(env.site_info.site_name))
    print(green("Backup FTP files on '{}'").format(env.host_string))
    path = Path(env.site_info.site_name, 'ftp')
    run('mkdir -p {0}'.format(path.remote_folder()))
    with cd(path.ftp_folder(env.site_info.site_name)):
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
    """Create a database.

    e.g:
    fab test:hatherleigh_info create_db

    Note: table space 'cbs' is the name we have given to the Rackspace Cloud
    Block Storage volume.  If you are not using cloud block storage, then don't
    use the 'table_space' parameter e.g:

    fab test:hatherleigh_info create_db:cbs
    """
    print(green("create '{}' database on '{}'").format(
        env.site_info.db_name, env.host_string
    ))
    if env.site_info.is_mysql:
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
        run('mysql -u root -e "CREATE DATABASE {};"'.format(database_name))
        # I had loads of problems with this one.  bash evaluates back-ticks
        # first.  I think I solved the issue by adding 'shell=False' to 'run'.
        command = (
            "GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, "
            "ALTER, LOCK TABLES, CREATE TEMPORARY TABLES ON \`{}\`.* TO "
            "'{}'@'localhost' IDENTIFIED BY '{}';".format(
                database_name, site_info.db_user(), site_info.password()
            )
        )
        run('mysql -u root -e "{}"'.format(command), shell=False)
    else:
        if not remote_user_exists(env.site_info):
            remote_user_create(env.site_info)
        remote_database_create(env.site_info, table_space)
    print(green('done'))


@task
def deploy(version):
    """ For docs, see https://github.com/pkimber/cloud_docs """
    env.user = 'web'
    folder_info = FolderInfo(env.site_info, version)
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
    if env.site_info.is_php:
        deploy_php(folder_info, env.site_info)
    else:
        deploy_django(folder_info, env.site_info, version)
    # symbolic link
    link_install_to_live_folder(folder_info.install(), folder_info.live())
    if env.site_info.is_django():
        django_post_deploy(folder_info)
    # Post deploy
    run_post_deploy_test(env.site_info)


@task
def drop_db(date_check=None):
    """Drop a database.

    You will need to enter the current date and time e.g:
    fab test:hatherleigh_info drop_db:02/02/2015-16:54
    """
    check = datetime.now().strftime('%d/%m/%Y-%H:%M')
    print(green("drop '{}' database on '{}'").format(
        env.site_info.db_name, env.host_string
    ))
    if check == date_check:
        message = "Are you sure you want to drop '{}' on '{}'?".format(
            env.site_info.db_name, env.host_string
        )
        confirm = prompt(
            "To drop the database, enter the name of the current month?"
        )
        check = datetime.now().strftime('%B')
        if not confirm == check:
            abort("exit... (the current month is '{}')".format(check))
        confirm = prompt("Are you sure you want to drop the database (Y/N)?")
        if confirm == 'Y':
            print('deleting...')
            if remote_database_exists(env.site_info):
                drop_remote_database(env.site_info)
            if remote_user_exists(env.site_info):
                drop_remote_user(env.site_info)
        else:
            abort("exit... (you did not enter 'Y' to drop the database)")
    else:
        print(
            "You cannot drop a database unless you enter the current date and "
            "time as a parameter e.g:\ndrop_db:{}".format(check)
        )

@task
def list_current(backup_or_files):
    duplicity = Duplicity(env.site_info, backup_or_files)
    duplicity.list_current()


@task
def reindex():
    """ For docs, see https://github.com/pkimber/cloud_docs """
    env.user = 'web'
    print(green("Haystack - reindex: '{}' on '{}' ").format(
        env.site_name, env.hosts
    ))
    folder_info = FolderInfo(env.site_info)
    command = DjangoCommand(
        folder_info.live(),
        folder_info.live_venv(),
        env.site_info
    )
    command.haystack_index()


@task
def restore(backup_or_files):
    duplicity = Duplicity(env.site_info, backup_or_files)
    duplicity.restore()


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
    folder_info = FolderInfo(name)
    command = DjangoCommand(
        folder_info.live(),
        folder_info.live_venv(),
        env.site_info
    )
    command.haystack_index_clear()


@task
def ok():
    """
    Test a live site (automatically done at the end of a deploy)

    e.g:
    fab -f deploy.py ok:name=csw_web
    """
    run_post_deploy_test(env.site_info)


def setup(domain):
    print(green("domain: {}".format(domain)))
    # find the server name for this site
    pillar_folder = get_pillar_folder()
    minion_id = get_server_name(pillar_folder, domain)
    print(yellow("minion_id: {}".format(minion_id)))
    env.site_info = SiteInfo(minion_id, domain)
    # Update env.hosts instead of calling execute()
    env.hosts = domain
    print(yellow("env.hosts: {}".format(env.hosts)))


@task
def domain(domain):
    """task for running commands on the site."""
    setup(domain)


@task
def kernel():
    print(yellow(env.site_name))
    run('uname -r')


@task
def valid():
    """ For docs, see https://github.com/pkimber/docs """
    SiteInfo(env.hosts, env.site_name)
    print(green(
        "The configuration for '{}' appears to be valid"
        "").format(env.site_name)
    )


@task
def solr_status():
    print(green("SOLR status: '{0}'").format(env.host_string))
    #run('curl http://localhost:8080/solr/status/')
    run('curl http://localhost:8080/solr/')
    #run('psql -X -U postgres -c "SELECT VERSION();"')


@task
def ssl():
    """ For docs, see https://github.com/pkimber/docs."""
    if not env.site_info.ssl:
        abort("'{}' is not set-up for SSL in the Salt pillar".format(env.site_info.domain))
    folder_info = FolderInfo(env.site_info)
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
        env.site_info.ssl_cert(),
        folder_info.ssl_cert(),
        use_sudo=True,
        mode=0400,
    )
    sudo('chown www-data:www-data {}'.format(folder_info.ssl_cert()))
    print(green(folder_info.ssl_cert()))
    put(
        env.site_info.ssl_server_key(),
        folder_info.ssl_server_key(),
        use_sudo=True,
        mode=0400,
    )
    sudo('chown www-data:www-data {}'.format(folder_info.ssl_server_key()))
    print(green(folder_info.ssl_server_key()))
    print(yellow("Complete"))


# Old code.
# See 'lib/duplicity.py' for the new code which restores from rsync.net
#
# @task
# def backup_db():
#     """For docs, see https://github.com/pkimber/docs"""
#     print(green("Backup '{}'").format(env.site_info.site_name))
#     db_type = 'postgres'
#     if env.site_info.is_mysql():
#         db_type = 'mysql'
#     path = Path(env.site_info.site_name, db_type)
#     run('mkdir -p {0}'.format(path.remote_folder()))
#     if env.site_info.is_mysql():
#         backup = env.site_info.backup()
#         run('mysqldump --host={} --user={} --password={} {} > {}'.format(
#             backup['host'],
#             backup['user'],
#             backup['pass'],
#             backup['name'],
#             path.remote_file(),
#         ))
#     else:
#         run('pg_dump -U postgres {0} -f {1}'.format(
#             env.site_info.site_name, path.remote_file()
#         ))
#     get(path.remote_file(), path.local_file())
#     if env.site_info.is_mysql():
#         pass
#     else:
#         print(green("restore to test database"))
#         if local_database_exists(path.test_database_name()):
#             local('psql -X -U postgres -c "DROP DATABASE {0}"'.format(path.test_database_name()))
#         local('psql -X -U postgres -c "CREATE DATABASE {0} TEMPLATE=template0 ENCODING=\'utf-8\';"'.format(path.test_database_name()))
#         if not local_postgres_user_exists(env.site_info.site_name):
#             local('psql -X -U postgres -c "CREATE ROLE {0} WITH PASSWORD \'{1}\' NOSUPERUSER CREATEDB NOCREATEROLE LOGIN;"'.format(env.site_info.site_name, env.site_info.site_name))
#         local("psql -X --set ON_ERROR_STOP=on -U postgres -d {0} --file {1}".format(
#             path.test_database_name(), path.local_file()), capture=True
#         )
#         local('psql -X -U postgres -d {} -c "REASSIGN OWNED BY {} TO {}"'.format(
#             path.test_database_name(), env.site_info.site_name, path.user_name()
#         ))
#         print(green("psql {}").format(path.test_database_name()))
#
# @task
# def db_version():
#     """
#     To find the Postgres version install on 'rs.db':
#     fab -H rs.db db_version
#     """
#     print(green("Postgres version installed on '{0}'").format(env.host_string))
#     run('psql -X -U postgres -c "SELECT VERSION();"')


