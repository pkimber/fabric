import os
import yaml

from pkg_resources import safe_name

from fabric.api import abort
from fabric.api import prompt
from fabric.colors import cyan
from fabric.colors import green
from fabric.colors import yellow
from fabric.colors import white

from walkdir import filtered_walk
from lib.scm.scm import Scm

FILENAME_SETUP_YAML = 'setup.yaml'


def check_is_project_or_app():
    """
    An app should have an 'project' folder or an 'example' folder.
    """
    print(yellow("check is app or project..."))
    found = False
    for name in ('project', 'example'):
        folder = os.path.join(os.getcwd(), name)
        if os.path.exists(folder) and os.path.isdir(folder):
            found = True
            break
    if not found:
        abort("Not a project or app (need a 'project' or 'example' folder)")


def check_scm_status():
    print(yellow("check version control status..."))
    scm = Scm(os.getcwd())
    status = scm.get_status()
    for name in status:
        if name not in ('setup.py',):
            abort('The following files have not been committed: {0}'.format(status))


def check_requirements(is_project, prefix):
    if is_project:
        print(yellow("check requirements.."))
        file_name = os.path.join(os.getcwd(), 'requirements-{}.txt'.format(prefix))
        if os.path.exists(file_name):
            with open(file_name) as f:
                content = f.readlines()
            print(white('Please check the app version numbers for this project:'))
            for line in content:
                name, version = line.strip().split('==')
                if name and version:
                    print(cyan('{:<30} {:<10}'.format(name, version)))
                else:
                    abort("Dependency in '{0}' does not have a name and version number: {1}".format(file_name, line))
            confirm = ''
            while confirm not in ('Y', 'N'):
                confirm = prompt("Are these the correct dependencies and versions (Y/N)?")
                confirm = confirm.strip().upper()
            if not confirm == 'Y':
                abort("Please check and correct the dependencies and their versions...")


def check_setup_yaml_exists():
    """ The file, 'setup.yaml' looks like the 'sample_data' below: """
    if not os.path.exists(FILENAME_SETUP_YAML):
        sample_data = {
            'description': 'User Auth',
            'name': 'user-auth',
            'version': '0.2.0',
        }
        abort("File '{0}' does not exist.  Please create in the following format:\n{1}".format(
            FILENAME_SETUP_YAML,
            yaml.dump(sample_data, default_flow_style=False)
        ))


def get_archive_name(sdist_out):
    archive_name = None
    for line in sdist_out.split('\n'):
        if line.startswith('creating'):
            archive_name = line[len('creating'):].strip()
            break
    if not archive_name:
        abort("Cannot find archive name in output of 'sdist' command")
    result = os.path.join('dist', '{0}.tar.gz'.format(archive_name))
    if not os.path.exists(result):
        abort("Cannot find archive name in the 'dist' folder: {0}".format(result))
    if not os.path.isfile(result):
        abort("Archive {0} is not a file.".format(result))
    return result


def get_description():
    print(yellow("get description..."))
    check_setup_yaml_exists()
    with open(FILENAME_SETUP_YAML) as f:
        data = yaml.load(f)
    if not 'description' in data:
        abort("Package 'description' not found in 'setup.yaml'")
    return data['description']


def get_scm_config():
    print(yellow("get version control config..."))
    scm = Scm(os.getcwd())
    return scm.get_config()


def get_name():
    check_setup_yaml_exists()
    with open(FILENAME_SETUP_YAML) as f:
        data = yaml.load(f)
    if not 'name' in data:
        abort("Package 'name' not found in 'setup.yaml'")
    return data['name']


def get_package_data(packages):
    print(yellow("get package data..."))
    result = {}
    for package in packages:
        if os.path.exists(package) and os.path.isdir(package):
            for folder_name in os.listdir(package):
                if folder_name in ('static', 'templates'):
                    folder = os.path.join(package, folder_name)
                    if os.path.isdir(folder):
                        walk = filtered_walk(folder)
                        for path, subdirs, files in walk:
                            if package not in result:
                                result[package] = []
                            # remove package folder name
                            result[package].append(os.path.join(*path.split(os.sep)[1:]))
    return result


def get_packages():
    print(yellow("get packages..."))
    walk = filtered_walk(
        '.',
        included_files=['__init__.py'],
        excluded_dirs=['.hg', 'dist', 'example', 'templates']
    )
    result = []
    for path, subdirs, files in walk:
        if len(files):
            path = path.replace(os.sep, '.').strip('.')
            if path:
                result.append('{0}'.format(path))
    for app_name in ("app", "example"):
        if app_name in result:
            result.remove(app_name)
            result.insert(0, app_name)
    return result


def get_next_version(current_version):
    elems = current_version.split('.')
    if not len(elems) == 3:
        abort("Current version number should contain only three sections: {}".format(current_version))
    for e in elems:
        if not e.isdigit():
            abort("Current version number should only contain numbers: {}".format(current_version))
    return '{}.{}.{:02d}'.format(elems[0], elems[1], int(elems[2]) + 1)


def get_version():
    check_setup_yaml_exists()
    with open(FILENAME_SETUP_YAML) as f:
        data = yaml.load(f)
    current_version = data['version']
    next_version = get_next_version(current_version)
    version = prompt(
        "Version number to release (previous {})".format(current_version),
        default=next_version,
        validate=validate_version
    )
    data['version'] = version
    with open(FILENAME_SETUP_YAML, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)
    print(green("Release version: {0}".format(version)))
    return version


def has_project_package(packages):
    if 'project' in packages:
        return True
    return False


def commit_and_tag(version):
    print(yellow("version control - commit and tag..."))
    scm = Scm(os.getcwd())
    scm.commit_and_tag(version)


def validate_version(version):
    elem = version.split('.')
    for e in elem:
        if not e.isdigit():
            raise Exception(
                "Not a valid version number: {0} (should contain only digits)".format(version))
    if not len(elem) == 3:
        raise Exception(
            "Not a valid version number: {0} (should contain three elements)".format(version))
    confirm = ''
    while confirm not in ('Y', 'N'):
        confirm = prompt("Please confirm you want to release version {0} (Y/N)".format(version))
        confirm = confirm.strip().upper()
    if confirm == 'Y':
        return version
    else:
        raise Exception("Please re-enter the version number")


def write_manifest_in(is_project, packages):
    print(yellow("write MANIFEST.in..."))
    folders = [
        'doc_src',
        'docs',
    ]
    for p in packages:
        if not '.' in p:
            folders = folders + [
                os.path.join('{0}'.format(p), 'static'),
                os.path.join('{0}'.format(p), 'templates'),
            ]
    content = []
    for f in folders:
        folder = os.path.join(os.getcwd(), f)
        if os.path.exists(folder) and os.path.isdir(folder):
            content.append('recursive-include {0} *'.format(f))
    content = content + [
        '',
        'include LICENSE',
    ]
    if is_project:
        content.append('include manage.py')
    content = content + [
        'include README',
        'include requirements/*.txt',
        'include *.txt',
        '',
        'prune example/',
    ]
    with open('MANIFEST.in', 'w') as f:
        f.write('\n'.join(content))


def write_setup(name, packages, package_data, version, url, author, email, description, prefix):
    """
    Prefix name so 'pip' doesn't get confused with packages on PyPI
    """
    print(yellow("write setup.py..."))
    content = """import os
from distutils.core import setup


def read_file_into_string(filename):
    path = os.path.abspath(os.path.dirname(__file__))
    filepath = os.path.join(path, filename)
    try:
        return open(filepath).read()
    except IOError:
        return ''


def get_readme():
    for name in ('README', 'README.rst', 'README.md'):
        if os.path.exists(name):
            return read_file_into_string(name)
    return ''


setup(
    name='%s-%s',
    packages=%s,%s
    version='%s',
    description='%s',
    author='%s',
    author_email='%s',
    url='%s',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Office/Business :: Scheduling',
    ],
    long_description=get_readme(),
)"""
    packages_delim = []
    for p in packages:
        packages_delim.append("'{0}'".format(p))
    data = ''
    if package_data:
        data = '\n    package_data={'
        for p, folders in package_data.items():
            data = data + "\n{}'{}': [\n".format(' ' * 8, p)
            folders.sort()
            for f in folders:
                data = data + "{}'{}',\n".format(' ' * 12, os.path.join(f, '*.*'))
            data = data + "{}],\n".format(' ' * 8)
        data = data + '    },'
    with open('setup.py', 'w') as f:
        f.write(content % (
            prefix,
            safe_name(name),
            '[{0}]'.format(', '.join(packages_delim)),
            data,
            version,
            description,
            author,
            email,
            url
        ))
