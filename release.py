from fabric.api import abort
from fabric.api import env
from fabric.api import local
from fabric.api import task
from fabric.colors import blue
from fabric.colors import green

from lib.dist.helper import check_is_project_or_app
from lib.dist.helper import check_requirements
from lib.dist.helper import check_scm_status
from lib.dist.helper import commit_and_tag
from lib.dist.helper import get_description
from lib.dist.helper import get_name
from lib.dist.helper import get_package_data
from lib.dist.helper import get_packages
from lib.dist.helper import get_scm_config
from lib.dist.helper import get_version
from lib.dist.helper import has_project_package
from lib.dist.helper import write_manifest_in
from lib.dist.helper import write_setup


# env.hosts = ['rs.master', ]
# env.use_ssh_config = True
# Set this to True and the version control checks and tags will be skipped
TESTING = False


@task
def dist(prefix, pypirc):
    """
    Upload release to our own python package index.

    - 'prefix' is for the company e.g. 'csw' or 'pkimber'.
    - 'pypirc' is the name of the pypi in your '~/.pypirc' file.

    e.g:
    fab -f /path/to/your/fabric/release.py dist:prefix=pkimber,pypirc=dev
    """
    print(green("release"))
    check_is_project_or_app()
    url, user, email = get_scm_config()
    if not TESTING:
        check_scm_status()
    description = get_description()
    packages = get_packages()
    package_data = get_package_data(packages)
    is_project = has_project_package(packages)
    name = get_name()
    check_requirements(is_project, prefix)
    version = get_version(TESTING)
    write_manifest_in(is_project, packages)
    write_setup(
        name,
        packages,
        package_data,
        version,
        url,
        user,
        email,
        description,
        prefix
    )
    if not TESTING:
        commit_and_tag(version)
        command = 'python setup.py clean sdist upload -r {}'.format(pypirc)
        print(blue(command))
        local(command)
