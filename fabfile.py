from fabric.api import cd
from fabric.api import *
from fabric.contrib.files import exists
import requests
import json
import os

env.user = 'doula'
env.key_filename = '~/.ssh/id_rsa_doula'
doula_dir = '/opt/bambino'
doula_address = 'http://doula.corp.surveymonkey.com/bambino/ip_addresses'

branch = 'master'

if "DOULA_STAGE" in os.environ:
    env.hosts = ['mt-99.corp.surveymonkey.com']
    branch = 'stage'

def update():
    if not exists(doula_dir):
        print "We can go no further, you must run 'fab create_env' before moving on"
        return

    with cd(doula_dir):
        if not exists('bin'):
            run('virtualenv .')
        with prefix('. bin/activate'):
            run('echo $VIRTUAL_ENV')
            run('pip install -e git+git://github.com/Doula/Bambino.git@%s#egg=bambino' % branch)
        with cd('src/bambino'):
            run('git submodule init')
            run('git submodule update')
        with cd('src/bambino/etc'):
            run('git checkout %s' % branch)
            run('git pull origin %s' % branch)
            restart()


def restart():
    run('supervisorctl reread bambino_6666')
    run('supervisorctl restart bambino_6666')


def create_env():
    _make_base_dir()


def get_hosts():
    # response = requests.get(doula_address)
    # response = json.loads(response.text)
    # print response
    response = {
        'ip_addresses': ['192.168.4.61', '192.168.4.58', '192.168.4.74', '192.168.4.41']
    }
    return response['ip_addresses']

if(len(env.hosts) == 0):
    print env.hosts
    env.hosts = get_hosts()
