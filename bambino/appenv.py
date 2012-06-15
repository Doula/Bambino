from git import Git
from contextlib import contextmanager
from git import GitCommandError
from git import Repo
from path import path as pathd
from socket import gethostname

import time
import datetime
import pkg_resources
import json
import sys
import traceback
import subprocess
import json
import os
import glob
import socket
import re

class Node(object):

    def __init__(self, root):
        self.root = root
        self.web_app_dir = WebAppDir(self.root)

    @property
    def repo_data(self):
        repos = []
        errors = []

        for folder in self.web_app_dir.services:
            try:
                repo = Application(folder)
                repos.append(repo.to_dict)
            except Exception, e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                errors.append({'path': str(folder), 'exception': "text: %s, traceback: %s" %
                    (str(e), str(traceback.extract_tb(exc_traceback)))})
        return {'services' :repos, 'errors' : errors}

    def tag_apps(self, apps_to_tag, tag, message):
        tagged_apps = []
        errors = []

        for folder in self.web_app_dir.services:
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

    @property
    def to_json(self):
        json.dumps(self.repo_data)

    @staticmethod
    def _ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.168.201.5",80))
        out = (s.getsockname()[0])
        s.close()
        return out

    @staticmethod
    def _hostname():
        from socket import gethostname
        return gethostname()

    @staticmethod
    def _site(hostname):
        sites = {'mktest3-py' : 'mt3', 'mktest2-py' : 'mt2', 'mktest2-py' : 'mt1'}
        if(hostname in sites):
            return sites[hostname]

        arr = hostname.split('-')
        if(len(arr) == 2):
            return arr[0]

        return hostname

    @staticmethod
    def get_machine_info():
        return {'ip' : Node._ip(), 'name' : Node._hostname(), 'site' : Node._site(Node._hostname())}

class WebAppDir(pathd):

    def __init__(self, filepath):
        super(WebAppDir, self).__init__(filepath)

    def is_env(self, folder):
        return (folder / '.git').exists() and (folder / 'etc').exists()

    @property
    def services(self):
        return (env for env in self.dirs() if self.is_env(env))

class Repository(object):

    def __init__(self, path):
        self.repo = Repo(path)
        self.path = path

    @property
    def last_tag(self):
        last_tag_name = None
        
        if len(self.repo.tags):
            last_tag_name = self.repo.tags.pop().name
        
        return self.repo.tags and last_tag_name or 'HEAD'
    
    @property
    def tags(self):
        tags = [ ]
        
        try:
            for tag in self.repo.tags:
                tag_details = { }
                
                if tag.tag:
                    tag_details['message'] = tag.tag.message
                    tag_details['date'] = tag.tag.tagged_date
                else:
                    tag_details['message'] = ''
                    tag_details['date'] = tag.commit.committed_date
                
                tag_details['name'] = tag.name
                tags.append(tag_details)
        except:
            # In case the tagged_date isn't available at all
            pass
        
        return tags
    
    @property
    def last_tag_message(self):
        last_tag_message = ''
        
        if len(self.repo.tags) > 0:            
            last_tag = self.repo.tags.pop()
            
            if last_tag.tag:
                last_tag_message = last_tag.tag.message
        
        return last_tag_message

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
        out['tags'] = self.tags
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
        
        return 'tagged'
    
    @property
    def to_dict(self):
        out = dict(self.repo_app.to_dict('app').items() + self.repo_config.to_dict('config').items())
        out['status'] = self.status
        out['name'] = self.name
        out['remote'] = self.remote
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
        if hasattr(self.remotes, 'origin'):
            return self.remotes.origin.url
        else:
            return ''
    
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
            pckg = {}
            
            if d.has_metadata('git_info.txt'):
                git_info_json = d.get_metadata('git_info.txt')
                git_info = json.loads(git_info_json)

                pckg['branch'] = git_info['git_branch']
                pckg['remotes'] = git_info['git_remotes']
            
            pckg['name'] = d.key
            pckg['version'] = d.version
            pckgs[d.key] = pckg

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
    

@contextmanager
def pushd(dir):
    old_dir = os.getcwd()
    os.chdir(dir)
    try:
        yield old_dir
    finally:
        os.chdir(old_dir)

