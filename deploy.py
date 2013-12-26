""" For docs, see https://github.com/pkimber/cloud_docs """
import os

from pkg_resources import safe_name

from fabric.api import abort
from fabric.api import env
from fabric.api import run
from fabric.api import task
from fabric.colors import green
from fabric.colors import yellow
from fabric.contrib.files import exists

from lib.browser.drive import BrowserDriver
from lib.manage.command import DjangoCommand
from lib.server.folder import FolderInfo
from lib.site.info import SiteInfo


env.use_ssh_config = True

SECRET_KEY = 'SECRET_KEY'


def download_package(site_name, prefix, version, temp_folder):
    package_name = '{}-{}=={}'.format(prefix, safe_name(site_name), version)
    print(green("download package: {}".format(package_name)))
    run('pip install --download={} --no-deps {}'.format(temp_folder, package_name))


def extract_project_package(install_folder, temp_folder, site_name, prefix, version):
    package_archive = '{}-{}-{}.tar.gz'.format(prefix, safe_name(site_name), version)
    print(green("extract project package: {}".format(package_archive)))
    run('tar --strip-components=1 --directory={} -xzf {}'.format(
        install_folder,
        os.path.join(temp_folder, package_archive)
        ))


def install_requirements(prefix, install_folder, venv_folder):
    """ Download python packages from our package index """
    filename = os.path.join(install_folder, 'requirements/production.txt')
    print(green("requirements: {}".format(filename)))
    pip_bin = os.path.join(venv_folder, 'bin', 'pip')
    run("{} install -r {}".format(pip_bin, filename))


def mkvirtualenv(venv_folder):
    print(green("mkvirtualenv: {0}".format(venv_folder)))
    run('/usr/bin/virtualenv {0}'.format(venv_folder))


def link_install_to_live_folder(install_folder, live_folder):
    print(green("link '{0}' folder to '{1}'".format(live_folder, install_folder)))
    if exists(live_folder):
        run('rm {0}'.format(live_folder))
    run('ln -s {0} {1}'.format(install_folder, live_folder))


def touch_vassal_ini(vassal_ini_file_name):
    print(green("touch: ".format(vassal_ini_file_name)))
    if exists(vassal_ini_file_name):
        run('touch {0}'.format(vassal_ini_file_name))
    else:
        abort('uwsgi ini file does not exist: {0}'.format(
            vassal_ini_file_name)
        )


def run_post_deploy_test(site_name):
    browser_driver = BrowserDriver(site_name)
    browser_driver.test()
    browser_driver.close()


def deploy_django(folder_info, site_info, prefix, version):
    # download and extract main package
    download_package(
        site_info.site_name(),
        prefix,
        version,
        folder_info.install_temp()
    )
    extract_project_package(
        folder_info.install(),
        folder_info.install_temp(),
        site_info.site_name(),
        prefix,
        version
    )
    # virtualenv
    mkvirtualenv(folder_info.install_venv())
    # debug
    run('ls -l {0}'.format(folder_info.install()))
    # requirements
    install_requirements(
        prefix, folder_info.install(), folder_info.install_venv()
    )
    command = DjangoCommand(
        folder_info.install(), folder_info.install_venv(), site_info
    )
    command.collect_static()
    # migrate database and init project
    command.syncdb()
    command.migrate_database()
    command.init_project()


def django_post_deploy(command, folder_info):
    # re-start uwsgi
    touch_vassal_ini(folder_info.vassal())


def deploy_php(folder_info, site_info):
    from fabric.contrib.project import rsync_project
    rsync_project(
        local_dir='/home/patrick/repo/wip/ilspa/deploy',
        remote_dir=folder_info.upload(),
    )

@task
def deploy(server_name, site_name, prefix, version):
    """ For docs, see https://github.com/pkimber/cloud_docs """
    site_info = SiteInfo(server_name, site_name)
    folder_info = FolderInfo(site_name, version)
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
        deploy_django(folder_info, site_info, prefix, version)
    # symbolic link
    link_install_to_live_folder(folder_info.install(), folder_info.live())
    if site_info.is_django():
        django_post_deploy(command, folder_info)
    # Post deploy
    # TODO add this back in!!
    # run_post_deploy_test(site_name)

@task
def ok(site_name):
    """
    Test a live site (automatically done at the end of a deploy)

    e.g:
    fab -f deploy.py ok:name=csw_web
    """
    run_post_deploy_test(site_name)
