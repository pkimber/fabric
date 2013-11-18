from git import Repo
from git.exc import InvalidGitRepositoryError

import hgapi


class ScmError(Exception):

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr('%s, %s' % (self.__class__.__name__, self.value))


class Scm(object):

    def __init__(self, folder):
        self.folder = folder
        self._is_hg = self.is_mercurial()
        if not self._is_hg:
            if not self.is_git():
                raise ScmError("Must be a Mercurial or GIT repository: {}".format(self.folder))

    def _get_hg_repo(self):
        return hgapi.Repo(self.folder)

    def _get_git_repo(self):
        return Repo(self.folder)

    def is_git(self):
        try:
            self._get_git_repo()
            return True
        except InvalidGitRepositoryError:
            return False

    def is_mercurial(self):
        result = False
        repo = self._get_hg_repo()
        try:
            repo.hg_status()
            result = True
        except hgapi.HgException as ev:
            if not 'no repository found' in ev.message:
                raise ScmError(
                    "Unexpected exception thrown by 'hg_status': {}".format(
                        ev.message
                    )
                )
        return result

    def get_config(self):
        if self._is_hg:
            repo = self._get_hg_repo()
            path = repo.config('paths', 'default')
            username = repo.config('ui', 'username')
            pos_start = username.find('<')
            pos_end = username.find('>')
            author = username[:pos_start].strip()
            email = username[pos_start + 1:pos_end]
            if 'bitbucket' in path:
                result = path, author, email
            else:
                raise ScmError('Cannot find bitbucket path to repository: {0}'.format(path))
        else:
            repo = self._get_git_repo()
            if len(repo.remotes) == 1:
                remote = repo.remotes[0]
                path = remote.url
                name = repo.config_reader(config_level="global").get("user", "name")
                email = repo.config_reader(config_level="global").get("user", "email")
                result = path, name, email
            else:
                raise ScmError("GIT repo has more than one remote.  Don't know what to do!")
        return result

    def get_status(self):
        result = []
        if self._is_hg:
            repo = self._get_hg_repo()
            for status, files in repo.hg_status().iteritems():
                for name in files:
                    result.append(name)
        else:
            repo = self._get_git_repo()
            out = repo.git.status('--porcelain')
            for line in out.splitlines():
                name = line.strip()
                pos = name.find(' ')
                if pos == -1:
                    raise ScmError("GIT status filename does not contain a space: {}".format(line))
                result.append(name[pos + 1:])
        return result

    def commit_and_tag(self, version):
        status = self.get_status()
        for name in status:
            pos = name.find(' ')
            if pos > -1:
                raise ScmError(
                    "Version control 'status' - filename contains a space: {}".format(name)
                )
        if(len(self.get_status())):
            message = "version {0}".format(version)
            tag = "{0}".format(version)
            if self._is_hg:
                repo = self._get_hg_repo()
                repo.hg_commit(message)
                repo.hg_tag(tag)
            else:
                repo = self._get_git_repo()
                index = repo.index
                index.add(status)
                index.commit(message)
                repo.create_tag(tag)
