from contextlib import contextmanager
from git import Git
from git import GitCommandError
from git import Repo
from path import path as pathd
from util import comparable_name
import json
import os
import pkg_resources
import re
import socket
import sys
import traceback


class Node(object):

    def __init__(self, root):
        self.root = root
        self.web_app_dir = WebAppDir(self.root)
        # self.java_dir = WebAppDir(os.path.join(self.root, "../java"))

    @property
    def repo_data(self):
        repos = []
        errors = []

        # Old code
        # for directory, language in {self.web_app_dir: 'python',  self.java_dir: 'java'}.iteritems():
        for directory, language in {self.web_app_dir: 'python'}.iteritems():
            r, e = self.repo_data_by_language(directory, language)
            repos = repos + r
            errors = errors + e

        return {'services': repos, 'errors': errors}

    def repo_data_by_language(self, directory, language):
        repos = []
        errors = []

        for subdir in directory.services:
            try:
                if language == 'python':
                    repo = Service(subdir)
                else:
                    repo = JavaService(subdir)
                repos.append(repo.to_dict)
            except Exception, e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                errors.append({'path': str(subdir), 'exception': "text: %s, traceback: %s" %
                    (str(e), str(traceback.extract_tb(exc_traceback)))})

        return (repos, errors)

    def tag_apps(self, apps_to_tag, tag, message):
        tagged_apps = []
        errors = []

        for folder in self.web_app_dir.services:
            if(folder.split('/')[-1] in apps_to_tag):
                try:
                    app = Service(folder)
                    # todo, use logging for this message
                    print 'tag:%s, message:%s' % (tag, message)
                    app.tag(tag, message)
                    tagged_apps.append(app.name)
                except Exception, e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    errors.append({
                        'path': str(folder),
                        'exception': "text: %s, traceback: %s" %
                            (str(e), str(traceback.extract_tb(exc_traceback)))
                        })

        return {'tagged_apps': tagged_apps, 'errors': errors}

    @property
    def to_json(self):
        json.dumps(self.repo_data)

    @staticmethod
    def _ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.168.201.5", 80))
        out = (s.getsockname()[0])
        s.close()
        return out

    @staticmethod
    def _hostname():
        from socket import gethostname
        return gethostname()

    @staticmethod
    def _site(hostname):
        sites = {'mktest3-py': 'mt3', 'mktest2-py': 'mt2'}
        if(hostname in sites):
            return sites[hostname]

        arr = hostname.split('-')
        if(len(arr) == 2):
            return arr[0]

        return hostname

    @staticmethod
    def get_machine_info():
        return {
            'ip': Node._ip(),
            'name': Node._hostname(),
            'site': Node._site(Node._hostname())
        }


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
        tags = []

        try:
            for tag in self.repo.tags:
                tag_details = {}

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
        if (self.path.endswith('/etc')):
            return Node._site(Node._hostname())
        else:
            return self.repo.head.reference.name

    @property
    def is_dirty(self):
        return self.repo.is_dirty()

    @property
    def changed_files(self):
        changed_files = []
        # Diff object between index and working tree
        diff = self.repo.index.diff(None)

        for d in diff:
            d_as_s = str(d)
            filename = d_as_s.split('============')[0].strip()

            if os.path.isfile(self.path + '/' + filename):
                changed_files.append(filename)

        return changed_files

    @property
    def change_count(self):
        try:
            _, count, _ = self.describe()
            return int(count)
        except GitCommandError:
            return 0

    ##########################
    # Show the Config Files
    ##########################

    @property
    def config(self):
        """
        Return the short sha1 of the etc directory. Used to check
        if the config files are up to date.
        """
        config = {}

        if (self.path.endswith('/etc')):
            try:
                git = Git(self.path)

                branch = self.current_branch
                config['branch'] = branch

                # Initial detatils, author, date, commit
                config.update(self._find_current_commit_details(git))

                config['repo_name'] = self._find_repo_name(git)

                # changed files
                config['changed_files'] = self._find_changed_files(git)
            except Exception as e:
                print 'ERROR PULLING DATA CONFIG FOR DIRECTORY: ' + self.path
                print e.message

        return config

    def _find_current_commit_details(self, git):
        """
        Find the current commit details (author, date and sha1)
        Example output from Git Command:
            git show --name-status
                commit ab81f0e16fc8304f2eea3595aedf549912b8510c
                Author: Chris George <chrisg@surveymonkey.com>
                Date:   Thu May 10 15:17:10 2012 -0700
                     Adding pricing back as a logger
                M       app.ini
        """
        try:
            commit_details = {
                "author": "",
                "sha": "",
                "date": "",
                "message": ""
            }

            commit_details["message"] = self._find_git_message(git)

            cmd = ['git', 'show', '--name-status']
            last_commit_text = git.execute(cmd)
            lines = last_commit_text.split("\n")

            for line in lines:
                if line.lower().startswith("commit"):
                    commit_details["sha"] = line.split(" ")[1]

                    cmd = ['git', 'show', '--format="%ci"', commit_details["sha"]]
                    date_text = git.execute(cmd)
                    commit_details["date"] = date_text.split("\n")[0].replace('"', '')

                if line.lower().startswith("author"):
                    commit_details["author"] = line.split(" ")[1]

            return commit_details
        except Exception as e:
            print 'ERROR TRYING TO GET COMMIT DETAILS'
            print e.message

            return commit_details

    def _find_git_message(self, git):
        try:
            cmd = ['git', 'log', '--oneline', '-1']
            text = git.execute(cmd)
            text_list = text.split(' ')
            msg = text_list[1:len(text_list)]
            return ' '.join(msg)
        except:
            return ''

    def _find_repo_name(self, git):
        """
        Find the name of the remote repo for the etc directory

        Example output from Git Command:
            origin  git@code.corp.surveymonkey.com:config/billweb.git (fetch)
            origin  git@code.corp.surveymonkey.com:config/billweb.git (push)

        Returns just 'billweb', the name of the remote repo
        """
        try:
            cmd = ['git', 'remote', '-v']
            text = git.execute(cmd)
            line = text.split("\n")[0]
            match = re.search(r'\/(\w+)\.git', line, re.I)

            if match:
                return match.groups()[0]
            else:
                # path will be something like /opt/webapp/anweb/etc
                return self.path.split('/')[-2]
        except Exception as e:
            print 'ERROR FINDING REPO NAME'
            print e.message

            return 'unknown_repo_name'

    def _find_changed_files(self, git):
        """
        Find the changed files in this repository

        Example Git Output
            git status -s, get changed and deleted files.
                D  .gitignore
                M  app.ini
                D  nginx.conf
                D  supervisor.conf
        """
        try:
            changed_files = {}
            cmd = ['git', 'status', '-s']
            status_text = git.execute(cmd)
            lines = status_text.split("\n")

            for line in lines:
                mod_match = re.search(r'm (.+)', line, re.I)

                if mod_match:
                    changed_files[mod_match.groups()[0]] = "modified"

                del_match = re.search(r'd (.+)', line, re.I)

                if del_match:
                    changed_files[del_match.groups()[0]] = "deleted"

            return changed_files
        except Exception as e:
            print 'ERROR GETTING CHANGED FILES'
            print e.message

            # return an empty dict
            return changed_files

    #########################
    # Output as a Dict
    #########################

    def to_dict(self, postfix):
        out = {}
        out['last_tag_%s' % postfix] = self.last_tag
        out['current_branch_%s' % postfix] = self.current_branch
        out['is_dirty_%s' % postfix] = self.is_dirty
        out['change_count_%s' % postfix] = self.change_count
        out['config'] = self.config
        out['tags'] = self.tags
        out['language'] = self.language

        if self.path.endswith('etc'):
            out['full_remote_etc'] = self.full_remote
        else:
            out['full_remote'] = self.full_remote

        return out

    @property
    def full_remote(self):
        # alextodo. wrap the calls to git commit
        repo = Git(self.path)
        cmd = ['git', 'remote', '-v']
        remote = repo.execute(cmd).split('(fetch)')[0]
        remote = remote or ''
        return remote.strip()

    @property
    def language(self):
        return 'java' if 'java' in str(self.path) else 'python'

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
        remote.push('refs/tags/%s:refs/tags/%s' % (tag, tag))


class Service(Repo):

    def __init__(self, filepath):
        super(Service, self).__init__(filepath)
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
        out['supervisor_service_names'] = self.supervisor_service_names(self.name)
        return out

    def supervisor_service_names(self, name):
        """
        Returns the service names found in the supevisor conf file.
        The supervisor.conf file is assumed to be in the /etc/supervisor/conf.d dir
        """
        conf_path = '/etc/supervisor/conf.d'
        conf_files = os.listdir(conf_path)
        supervisor_service_names = []
        name = comparable_name(name)

        for conf_file in conf_files:
            comparable_file_name = comparable_name(conf_file)
            # Compare without the dot in the name, makes it
            # possible to compare oddly named values
            if comparable_file_name == name or comparable_file_name == name + 'conf':
                with file(conf_path + '/' + conf_file) as f:
                    for line in f.readlines():
                        match = re.match(r'\[program:([\w\d]+)\]', line, re.I)

                        if match:
                            supervisor_service_names.append(match.groups()[0])

        return supervisor_service_names

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
        return [x for x in changed_files if x not in seen and not seen_add(x)]

    @property
    def packages(self):
        """
        Returns a list of pkg_resources.Distribution objects.
        We'll use these to query the name and versions for that environment.
        """
        site_pckg_path = self._get_site_pckg_path(self.path)
        dists = pkg_resources.find_distributions(site_pckg_path)
        pckgs = {}

        for d in dists:
            pckg = {}
            pckg['name'] = d.key
            pckg['version'] = d.version
            pckgs[d.key] = pckg

        return pckgs

    def _get_site_pckg_path(self, filepath):
        lib_dir = pathd(filepath + '/lib')
        # Use python* because we don't know which version of python
        # we're looking for
        python_dir = lib_dir.dirs('python*')[0]
        site_pckg_path = python_dir + '/site-packages'

        return site_pckg_path

    def tag(self, tag, description):
        self.app.tag(tag, description)
        self.etc.tag(tag, description)


class JavaService(Service):

    def __init__(self, filepath):
        super(JavaService, self).__init__(filepath)

    @property
    def packages(self):
        pckgs = {}
        version_file = os.path.join(self.path, 'version.json')
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                read_data = f.read()
            version = json.loads(read_data)
            pckgs[str(self.name)] = version['version']

        return pckgs


@contextmanager
def pushd(dir):
    old_dir = os.getcwd()
    os.chdir(dir)
    try:
        yield old_dir
    finally:
        os.chdir(old_dir)
