import os
import glob
import shutil
import subprocess
import tempfile
import unittest

from bambino.appenv import *
from bambino.appenv import Repository
from contextlib import contextmanager
from pprint import pprint as pp
from path import path

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
        return WebAppDir(self.sandbox)

    def test_envid(self):
        aef = self.makeone()
        assert aef.applications
        envs = set(x.name for x in aef.applications)
        assert envs == set(('ae1', 'ae2')), envs

class TestAppEnvRepo(unittest.TestCase):
    temp_dir = os.getcwd() + '/temp'
    temp_etc_dir = temp_dir + '/etc'

    def setUp(self):
        # Create a simulated app env directory
        if not os.path.isdir(TestAppEnvRepo.temp_etc_dir):
            os.makedirs(TestAppEnvRepo.temp_etc_dir)

    def tearDown(self):
        # Remove the directory
        if os.path.isdir(TestAppEnvRepo.temp_dir):
            shutil.rmtree(TestAppEnvRepo.temp_dir, True)


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

            from bambino.appenv import Application
            return Application(sb)

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
        assert repo.status == 'change_to_app_and_config'

    def test_add_note(self):
        """
        Test adding a note to an app environment.
        """
        msg = "Add this message to Bambino"
        app = Application(TestAppEnvRepo.temp_dir)
        app.add_note(msg)
        
        files = glob.glob(TestAppEnvRepo.temp_dir + '/data/*_note.txt')
        
        self.assertTrue(len(files) > 0)
    def test_mark_tag_as_deployed(self):
        app = Application(TestAppEnvRepo.temp_dir)
        app.mark_tag_as_deployed('test_tag')

        self.assertTrue(app.is_tag_deployed('test_tag'))


@contextmanager
def pushd(dir):
    old_dir = os.getcwd()
    os.chdir(dir)
    try:
        yield old_dir
    finally:
        os.chdir(old_dir)

if __name__ == '__main__':
    unittest.main()