from git import Git
from contextlib import contextmanager
from git import GitCommandError
from git import Repo
from path import path as pathd

import time
import datetime
import pkg_resources
import json
import sys
import traceback
import subprocess
import os
import glob

class Node(object):

    def __init__(self, root):
        self.root = root
        self.web_app_dir = WebAppDir(self.root)

    @property
    def repo_data(self):
        repos = []
        errors = []

        for folder in self.web_app_dir.applications:
            try:
                repo = Application(folder)
                repos.append(repo.to_dict)
            except Exception, e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                errors.append({'path': str(folder), 'exception': "text: %s, traceback: %s" %
                    (str(e), str(traceback.extract_tb(exc_traceback)))})
        return {'applications' :repos, 'errors' : errors}

    def tag_apps(self, apps_to_tag, tag, message):
        tagged_apps = []
        errors = []

        for folder in self.web_app_dir.applications:
            if(folder.split('/')[-1] in apps_to_tag):
                try:
                    app = Application(folder)
                    # todo, use logging for this message
                    print 'tag:%s, message:%s' % (tag, message)
                    app.tag(tag, message)
                    tagged_apps.append(app.name)
                except Exception, e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    errors.append({'path': str(folder), 'exception': "text: %s, traceback: %s" %
                        (str(e), str(traceback.extract_tb(exc_traceback)))})
        return {'tagged_apps' :tagged_apps, 'errors' :errors}

    def add_note(self, app, note):
        """
        Add a note to a specific application.
        """
        # alextodo, handle exceptions. for now okay to throw exception, 501 error
        for folder in self.web_app_dir.applications:
            if(folder.split('/')[-1] == app):
                app = Application(folder)
                app.add_note(note)

    @property
    def to_json(self):
        json.dumps(self.repo_data)

class WebAppDir(pathd):

    def __init__(self, filepath):
        super(WebAppDir, self).__init__(filepath)

    def is_env(self, folder):
        return (folder / '.git').exists() and (folder / 'etc').exists()

    @property
    def applications(self):
        return (env for env in self.dirs() if self.is_env(env))

class Repository(object):

    def __init__(self, path):
        self.repo = Repo(path)
        self.path = path

    @property
    def last_tag(self):
        return self.repo.tags and self.repo.tags.pop().name or 'HEAD'

    @property
    def last_tag_message(self):
        last_tag = self.repo.tags.pop()
        return last_tag.tag.message

    @property
    def current_branch(self):
        return self.repo.head.reference.name

    @property
    def is_dirty(self):
        return self.repo.is_dirty()
    
    @property
    def changed_files(self):
        changed_files = [ ]
        # Diff object between index and working tree
        diff = self.repo.index.diff(None)
        
        for d in diff:
            d_as_s = str(d)
            filename = d_as_s.split('============')[0].strip()
            changed_files.append(filename)
        
        return changed_files

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
        result = repo.execute(cmd).split('-')
        if (len(result) == 1):
            return '', 0, ''
        else:
            howmany, sha = result[-2:]
            branch = '-'.join(result[0:len(result) - 2])
            return branch, howmany, sha

    def tag(self, tag, description):
        repo = Repo(self.path)
        repo.create_tag(tag, message=description)
        remote = repo.remote()
        # alextodo what happens when this fails? can we have a reconciliation
        # where any tags that haven't been pushed go up?
        remote.push('refs/tags/%s:refs/tags/%s' % (tag, tag))

class Application(Repo):

    def __init__(self, filepath):
        super(Application, self).__init__(filepath)
        self.path = pathd(filepath)
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
        out['remote'] = self.remote
        out['notes'] = self.notes
        out['packages'] = self.packages
        out['changed_files'] = self.changed_files
        out['last_tag_message'] = self.repo_app.last_tag_message
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

    @property
    def remote(self):
        return self.remotes.origin.url
    
    @property
    def changed_files(self):
        changed_files = self.repo_app.changed_files
        changed_files.extend(self.repo_config.changed_files)

        return self._unique_files(changed_files)

    def _unique_files(self, changed_files):
        seen = set()
        seen_add = seen.add
        return [ x for x in changed_files if x not in seen and not seen_add(x)]
    
    @property
    def packages(self):
        """
        Returns a list of pkg_resources.Distribution objects.
        We'll use these to query the name and versions for that environment.
        """
        site_pckg_path = self._get_site_pckg_path(self.path)
        dists = pkg_resources.find_distributions(site_pckg_path)
        pckgs = { }

        for d in dists:
            pckgs[d.key] = d.version

        return pckgs

    def _get_site_pckg_path(self, filepath):
        lib_dir = pathd(filepath + '/lib')
        # Use python* because we don't know which version of python
        # we're looking for
        python_dir = lib_dir.dirs('python*')[0]
        site_pckg_path =  python_dir + '/site-packages'

        return site_pckg_path

    def tag(self, tag, description):
        self.app.tag(tag, description)
        self.etc.tag(tag, description)

    def mark_tag_as_deployed(self, tag):
        """
        Adds tag to the end of the file ./data/deploy.txt
        thus marking it as deployed.
        """
        # alextodo, this data needs to be sent to the git repo
        self._ensure_data_directory_exist()
        f = open(self.path + '/data/deploy.txt', 'a')
        f.write(tag + "\n")
        f.close()
    
    def is_tag_deployed(self, tag):
        f = open(self.path + '/data/deploy.txt', 'r')
        for line in f.readlines():
            if line.strip() == tag:
                return True
        
        return False
    
    @property
    def notes(self):
        """
        Return a list of the notes that exist in the data directory.
        """
        notes = glob.glob(self.path + '/data/*_note.txt')
        notes_and_text = { }

        for note_path in notes:
            f = open(note_path)
            date = os.path.basename(note_path).replace('_note.txt', '')
            notes_and_text[date] = f.read()
            f.close()

        return notes_and_text

    def add_note(self, msg):
        """
        Add a new note to data directory.
        # alextodo, need to push up change. for now just make change
        """
        self._ensure_data_directory_exist()
        note_name = self._get_note_name()
        self._write_note(msg, note_name)
        # alextodo push to git, move it up to code.corp.
    
    def _write_note(self, msg, note_name):
        f = open(self.path + '/data/' + note_name, 'w')
        f.write(msg)
        f.close()

    def _get_note_name(self):
        """
        Return the name of the next note. The format of the
        name is YYYYMMDDHHMMSS_note.txt (UTC timestamp)
        """
        utc = datetime.datetime.utcfromtimestamp(time.time())
        format = "%Y%m%d%H%M%S"
        return utc.strftime(format) + '_note.txt'

    def _ensure_data_directory_exist(self):
        if not os.path.isdir(self.path + '/data'):
            os.makedirs(self.path + '/data')

@contextmanager
def pushd(dir):
    old_dir = os.getcwd()
    os.chdir(dir)
    try:
        yield old_dir
    finally:
        os.chdir(old_dir)

