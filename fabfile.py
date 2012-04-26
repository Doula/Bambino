from fabric.api import local
from fabric.api import cd
from fabric.api import *
from fabric.contrib.files import exists
from fabric.context_managers import settings
import requests
import json

env.hosts = []
env.user = 'doula'
env.key_filename = '~/.ssh/id_rsa'
doula_dir = '/opt/bambino'
doula_address = 'http://doula.corp.surveymonkey.com/nodes/ip_addresses'
supervisor_file = '/etc/supervisor/conf.d/bambino.conf'

def update():
    if not exists(doula_dir):
        print "We can go no further, you must run 'fab create_env' before moving on"
        return

    with cd(doula_dir):
        if not exists('bin'):
            run('virtualenv .')
        with prefix('. bin/activate'):
            run('echo $VIRTUAL_ENV')
            run('pip install -e git+git://github.com/Doula/Doula.git#egg=bambino')
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
    sudo('supervisorctl reread bambino_6666')
    sudo('supervisorctl restart bambino_6666')

def create_env(host='mktest1-pyweb.corp.surveymonkey.com'):
    _make_base_dir()

def get_hosts():
    response = requests.get(doula_address)
    response = json.loads(response.text)
    return response['ip_addresses']

env.hosts = get_hosts()
