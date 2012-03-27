from git import Git
from git import GitCommandError
from git import Repo
from path import path
import json
import sys
import traceback

class AppEnv(object):

    def __init__(self, root):
        self.root = root

    @property
    def repo_data(self):
        folders = AppEnvFolder(self.root)
        repos = []
        errors = []
        for folder in folders.envs:
            try:
                repo = AppEnvRepo(folder)
                repos.append(repo.to_dict)
            except Exception, e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                errors.append({'path': str(folder), 'exception': "text: %s, traceback: %s" % 
                    (str(e), str(traceback.extract_tb(exc_traceback)))})
        return {'applications' :repos, 'errors' : errors}

    @property
    def to_json(self):
        json.dumps(self.repo_data)

class AppEnvFolder(path):

    def __init__(self, filepath):
        super(AppEnvFolder, self).__init__(filepath)

    def is_env(self, folder):
        return (folder / '.git').exists() and (folder / 'etc').exists()

    @property
    def envs(self):
        return (env for env in self.dirs() if self.is_env(env))

class RepoWrapper(object):

    def __init__(self, path):
        self.repo = Repo(path)
        self.path = path

    @property
    def last_tag(self):
        return self.repo.tags and self.repo.tags.pop().name or 'HEAD'

    @property
    def current_branch(self):
        return self.repo.head.reference.name

    @property
    def is_dirty(self):
        return self.repo.is_dirty()

    @property
    def change_count(self):
        try:
            _, count, _ = self.describe()
            return int(count)
        except GitCommandError:
            return 0

    def to_dict(self, postfix):
        out = {}
        out['last_tag_%s' % postfix] = self.last_tag
        out['current_branch_%s' % postfix] = self.current_branch
        out['is_dirty_%s' % postfix] = self.is_dirty
        out['change_count_%s' % postfix] = self.change_count
        return out

    def describe(self):
        repo = Git(self.path)
        cmd = ['git', 'describe', '--tags']
        branch, howmany, sha = repo.execute(cmd).split('-')
        return branch, howmany, sha

class AppEnvRepo(Repo):

    def __init__(self, filepath):
        super(AppEnvRepo, self).__init__(filepath)
        self.path = path(filepath)
        self.repo_app = RepoWrapper(self.path)
        self.repo_config = RepoWrapper(self.path / 'etc')

    @property
    def status(self):
        if self.repo_app.is_dirty and self.repo_config.is_dirty:
            return 'uncommitted_changes'

        if (self.repo_app.change_count + self.repo_config.change_count > 0):
            if (self.repo_app.change_count > 0 and self.repo_config.change_count > 0):
                return 'change_to_app_and_config'
            if (self.repo_app):
                return 'change_to_app'
            else:
                return 'change_to_config'

        return 'unchanged'

    @property
    def to_dict(self):
        out = dict(self.repo_app.to_dict('app').items() + self.repo_config.to_dict('config').items())
        out['status'] = self.status
        out['name'] = self.name
        return out

    @property
    def app(self):
        return self.repo_app

    @property
    def etc(self):
        return self.repo_etc

    @property
    def name(self):
        return self.path.basename()