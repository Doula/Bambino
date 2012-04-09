from git import Git
from contextlib import contextmanager
from git import GitCommandError
from git import Repo
from path import path
import json
import sys
import traceback
import subprocess
import os

class Node(object):

    def __init__(self, root):
        self.root = root

    @property
    def repo_data(self):
        web_app_dir = WebAppDir(self.root)
        repos = []
        errors = []
        for folder in web_app_dir.applications:
            try:
                repo = Application(folder)
                repos.append(repo.to_dict)
            except Exception, e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                errors.append({'path': str(folder), 'exception': "text: %s, traceback: %s" % 
                    (str(e), str(traceback.extract_tb(exc_traceback)))})
        return {'applications' :repos, 'errors' : errors}

    def tag_apps(self, apps_to_tag, tag, message):
        web_app_dir = WebAppDir(self.root)
        tagged_apps = []
        errors = []
        for folder in web_app_dir.applications:
            if(folder.split('/')[-1] in apps_to_tag):
                try:
                    app = Application(folder)
                    app.tag(tag, message)
                    tagged_apps.append(app.name)
                except Exception, e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    errors.append({'path': str(folder), 'exception': "text: %s, traceback: %s" % 
                        (str(e), str(traceback.extract_tb(exc_traceback)))})
        return {'tagged_apps' :tagged_apps, 'errors' :errors}

    @property
    def to_json(self):
        json.dumps(self.repo_data)

class WebAppDir(path):

    def __init__(self, filepath):
        super(WebAppDir, self).__init__(filepath)

    def is_env(self, folder):
        return (folder / '.git').exists() and (folder / 'etc').exists()

    @property
    def applications(self):
        return (env for env in self.dirs() if self.is_env(env))

class Pip(object):

    def __init__(self, root):
        self.root = root

    def freeze(self):
        with pushd(self.root):
            output,_ = subprocess.Popen(['pip', 'freeze', '-E', self.root], shell=False, stdout=subprocess.PIPE).communicate().split('\n')
            lists = [split('==') for x in a.split('\n')]


class Repository(object):

    def __init__(self, path):
        self.repo = Repo(path)
        self.path = path

    @property
    def last_tag(self):
        return self.repo.tags and self.repo.tags.pop().name or 'HEAD'

    @property
    def current_branch(self):
        import pdb; pdb.set_trace();
        return self.repo.head.reference.name

    @property
    def is_dirty(self):
        return self.repo.is_dirty()

    @property

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
        #branch, howmany, sha = repo.execute(cmd).split('-')
        result = repo.execute(cmd).split('-')
        howmany, sha = result[-2:]
        branch = '-'.join(result[0:len(result) - 2])
        return branch, howmany, sha

    def tag(self, tag, description):
        repo = Repo(self.path)
        repo.create_tag(tag, message=description)
        remote = repo.remote()
        remote.push('refs/tags/%s:refs/tags/%s' % (tag, tag))

class Application(Repo):

    def __init__(self, filepath):
        super(Application, self).__init__(filepath)
        self.path = path(filepath)
        self.repo_app = Repository(self.path)
        etc = (self.path / 'etc').abspath()
        self.repo_config = Repository(etc)

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
        return self.repo_config

    @property
    def name(self):
        return self.path.basename()

    def tag(self, tag, description):
        self.app.tag(tag, description)
        self.etc.tag(tag, description)

@contextmanager
def pushd(dir):
    old_dir = os.getcwd()
    os.chdir(dir)
    try:
        yield old_dir
    finally:
        os.chdir(old_dir)


