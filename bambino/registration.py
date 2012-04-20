import atexit
import json
import time
import logging
import requests
import sys
from sys import exit
from signal import signal, SIGTERM, SIGINT
from apscheduler.scheduler import Scheduler

module = sys.modules[__name__]
log = logging.getLogger('bambino')
sched = Scheduler()
node = { }
registration_url = ''

def register_shutdown():
    """
    Unregister Bambino on shutdown.
    """
    try:
        payload = { 'node': json.dumps(node), 'action': 'unregister' }
        requests.post(registration_url, data=payload)
    except requests.exceptions.ConnectionError as e:
        log.error(e.message)

def register_bambino(n, url):
    """
    Start the Bambino heart beat to let Doula know that
    this node is alive.
    """
    setattr(module, 'node', n)
    setattr(module, 'registration_url', url)
    
    sched.start()

    # Observe the death of this application
    signal(SIGTERM, lambda signum, stack_frame: exit(1))
    signal(SIGINT, lambda signum, stack_frame: exit(1))
    atexit.register(register_shutdown)

@sched.interval_schedule(seconds=5)
def job_function():
    """
    Register this nodes data, i.e.
    {
    'name':value,
    'site':value,
    'url':value
    }
    """
    try:
        payload = { 'node': json.dumps(node), 'action': 'register' }
        requests.post(registration_url, data=payload)
    except requests.exceptions.ConnectionError as e:
        log.error(e.message)