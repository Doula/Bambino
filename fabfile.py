from fabric.api import local
from fabric.api import cd
from fabric.api import *
from fabric.contrib.files import exists
from fabric.context_managers import settings

env.hosts = []
env.user = 'doula'
env.key_filename = '~/.ssh/id_rsa'
doula_dir = '/opt/bambino'
supervisor_file = '/etc/supervisor/conf.d/bambino.conf'

def update():
    if not exists(doula_dir):
        print "We can go no further, you must run 'fab create_env' before moving on"
        return

    with cd(doula_dir):
        if not exists('bin'):
            run('mkvirtualenv .')
        with prefix('. bin/activate'):
            run('echo $VIRTUAL_ENV')
            run('pip install -e git+git@github.com:Doula/Bambino.git#egg=bambino')
        with cd('src/bambino'):
            run('git submodule init')
            run('git submodule update')
        with cd('src/bambino/etc'):
            run('git checkout master')
            run('git pull origin master')
            if exists(supervisor_file):
                sudo('rm %s' % supervisor_file)
            sudo('ln -s $(pwd)/supervisor.conf %s' % supervisor_file)
        restart()

def restart():
    sudo('supervisorctl restart bambino_6666')

def create_env(host='mktest1-pyweb.corp.surveymonkey.com'):
    _make_base_dir()

def _make_base_dir():
    if not exists(doula_dir):
        sudo('mkdir %s' % doula_dir)
        sudo('chown doula:root %s' % doula_dir)
        sudo('chmod 0775 %s' % doula_dir)

def get_hosts():
    #TODO: delete this line when alex's stuff returns hosts
    return ['10.100.1.23']

def _get_host_from_user():
    i = raw_input("Enter the ip for your target host OR leave blank to ask Doula for all hosts.\n> ")
    if (i==""):
        return get_hosts()
    else:
        return [i]

env.hosts = _get_host_from_user()
