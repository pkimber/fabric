""" For docs, see https://github.com/pkimber/cloud_docs """
import os

from pkg_resources import safe_name

from fabric.api import abort
from fabric.api import env
from fabric.api import run
from fabric.api import task
from fabric.colors import green
#from fabric.colors import yellow
from fabric.contrib.files import exists

from lib.browser.drive import BrowserDriver
from lib.manage.command import DjangoCommand
from lib.server.folder import FolderInfo
from lib.site.info import SiteInfo


env.use_ssh_config = True

SECRET_KEY = 'SECRET_KEY'


def download_package(prefix, name, version, temp_folder):
    package_name = '{}-{}=={}'.format(prefix, safe_name(name), version)
    print(green("download package: {}".format(package_name)))
    run('pip install --download={} --no-deps {}'.format(temp_folder, package_name))


def extract_project_package(install_folder, temp_folder, prefix, name, version):
    package_archive = '{}-{}-{}.tar.gz'.format(prefix, safe_name(name), version)
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


def run_post_deploy_test(name):
    browser_driver = BrowserDriver(name)
    browser_driver.test()
    browser_driver.close()


@task
def deploy(prefix, name, version):
    """ For docs, see https://github.com/pkimber/cloud_docs """
    site_info = SiteInfo(prefix, name)
    # folder names
    folder_info = FolderInfo(name, version)
    install_folder = folder_info.install()
    temp_folder = folder_info.install_temp()
    venv_folder = folder_info.install_venv()
    # django command runner
    command = DjangoCommand(install_folder, venv_folder, site_info)
    # validate
    if exists(install_folder):
        raise Exception('Install folder {0} already exists'.format(install_folder))
    print(green(install_folder))
    # create folders
    if not exists(folder_info.deploy()):
        run('mkdir {0}'.format(folder_info.deploy()))
    run('mkdir {0}'.format(install_folder))
    run('mkdir {0}'.format(temp_folder))
    # download and extract main package
    download_package(prefix, name, version, temp_folder)
    extract_project_package(install_folder, temp_folder, prefix, name, version)
    # virtualenv
    mkvirtualenv(venv_folder)
    # debug
    run('ls -l {0}'.format(install_folder))
    # requirements
    install_requirements(prefix, install_folder, venv_folder)
    # collect static
    command.collect_static()
    # symbolic link
    link_install_to_live_folder(install_folder, folder_info.live())
    # migrate database and init project
    command.syncdb()
    command.migrate_database()
    command.init_project()
    # re-start uwsgi
    touch_vassal_ini(folder_info.vassal())
    # Post deploy
    run_post_deploy_test(name)


@task
def ok(name):
    """
    Test a live site (automatically done at the end of a deploy)

    e.g:
    fab -f deploy.py ok:name=csw_web
    """
    run_post_deploy_test(name)
