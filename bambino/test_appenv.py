from contextlib import contextmanager
from bambino.appenv import RepoWrapper
import os
import subprocess
from path import path
import tempfile
import unittest
from pprint import pprint as pp

class TestAppEnvIdentification(unittest.TestCase):

    def setUp(self):
        sb = self.sandbox = path(tempfile.mkdtemp())
        ae1 = sb / 'ae1'
        ae2 = sb / 'ae2'
        ne1 = sb / 'ne2'
        for env in ae1, ae2:
            (env / '.git').makedirs_p()
            (env / 'etc').mkdir()
        ne1.mkdir()

    def makeone(self):
        from bambino import appenv
        return appenv.AppEnvFolder(self.sandbox)

    def test_envid(self):
        aef = self.makeone()
        assert aef.envs
        envs = set(x.name for x in aef.envs)
        assert envs == set(('ae1', 'ae2')), envs

class TestAppEnvRepo(unittest.TestCase):

    def make_env_app(self, args=[]):
        sb = self.sandbox = path(tempfile.mkdtemp())
        with pushd(sb):
            predefined=['git init', 'touch root.txt', 'git add .',
                        'git commit -a -m "commit to root"',
                        'mkdir etc', 'cd etc',
                        'git init', 'touch etc.txt', 'git add .',
                        'git commit -a -m "commit to etc"',
                        'cd ..']

            devnul = '| > /dev/null 2>&1'

            for deffed in predefined:
                subprocess.check_output(deffed + devnul,  shell=True)

            for arg in args:
                subprocess.check_output(arg + devnul, shell=True)

            from bambino.appenv import AppEnvRepo
            return AppEnvRepo(sb)

    def test_no_tag(self):
        repo = self.make_env_app()
        assert repo.app.last_tag == 'HEAD'

    def test_dirty(self):
        repo = self.make_env_app(['echo "hi" >> root.txt'])
        assert repo.app.is_dirty == True, repo

    def test_change_count(self):
        args = ['echo "hi" >> root.txt', 'git tag first_tag', 'git commit -a -m "im just saying"']
        repo = self.make_env_app(args)
        assert repo.app.change_count == 1, details

    def test_current_branch(self):
        args = ['git checkout -b my_branch']
        repo = self.make_env_app(args)
        assert repo.app.current_branch == 'my_branch', details

    def test_unchanged(self):
        repo = self.make_env_app()
        assert repo.status == 'unchanged'

    def test_uncommitted_changes(self):
        args = ['echo "hi" >> root.txt']
        repo = self.make_env_app(args)
        assert repo.status == 'uncommitted_changes'

    def test_committed_changes(self):
        args = ['echo "hi" >> root.txt',
                'git tag first_tag',
                'git commit -a -m "im just saying"']
        repo = self.make_env_app(args)
        import pdb; pdb.set_trace()
        assert repo.status == 'change_to_app'

@contextmanager
def pushd(dir):
    old_dir = os.getcwd()
    os.chdir(dir)
    try:
        yield old_dir
    finally:
        os.chdir(old_dir)