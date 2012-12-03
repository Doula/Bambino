from bambino.appenv import *
from contextlib import contextmanager
from path import path
import os
import shutil
import subprocess
import tempfile
import unittest


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
        assert aef.services
        envs = set(x.name for x in aef.services)
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

    def test_config_billweb(self):
        """
        Test the Repository.config property. This test WILL NOT
        be a true unit test because it requires a Git repository
        """
        git_path = '/opt/webapp/billweb/etc'
        repository = Repository(git_path)
        config = repository.config

        self.assertTrue(config["author"])
        self.assertTrue(config["date"])
        self.assertTrue(config["commit"])
        self.assertTrue(config["latest_commit"])
        self.assertTrue(config["changed_files"])

    def test_config_anweb(self):
        """
        Test the Repository.config property. This test WILL NOT
        be a true unit test because it requires a Git repository
        """
        git_path = '/opt/webapp/anweb/etc'
        repository = Repository(git_path)
        config = repository.config

        self.assertTrue(config["author"])
        self.assertTrue(config["date"])
        self.assertTrue(config["commit"])
        self.assertTrue(config["latest_commit"])
        self.assertTrue(config["changed_files"])

    def make_env_app(self, args=[]):
        sb = self.sandbox = path(tempfile.mkdtemp())
        with pushd(sb):
            predefined = ['git init', 'touch root.txt', 'git add .',
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

            from bambino.appenv import Service
            return Service(sb)

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
        assert repo.status == 'tagged'

    def test_uncommitted_changes(self):
        args = ['echo "hi" >> root.txt']
        repo = self.make_env_app(args)
        assert repo.status == 'uncommitted_changes'

    def test__get_latest_commit_sha1_from_log(self):
        git_path = '/opt/webapp/billweb/etc'
        repository = Repository(git_path)
        log_text = """commit 0fab9fbd022c71d4883dc153c2730f771b534c0a
            Author: Doug Morgan <doug@surveymonkey.com>
            Date:   Tue Nov 13 11:30:22 2012 -0800

                Update app.ini

                Testing changing path"""
        sha1 = repository._get_latest_commit_sha1_from_log(log_text)
        self.assertEqual(sha1, '0fab9fbd022c71d4883dc153c2730f771b534c0a')

    def test_committed_changes(self):
        args = ['echo "hi" >> root.txt',
                'git tag first_tag',
                'git commit -a -m "im just saying"']
        repo = self.make_env_app(args)
        assert repo.status == 'change_to_app_and_config'


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
