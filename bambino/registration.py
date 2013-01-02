import atexit
import json
import logging
import requests
from sys import exit
from signal import signal, SIGTERM, SIGINT, SIGHUP
from apscheduler.scheduler import Scheduler

log = logging.getLogger('bambino')
log.setLevel(logging.ERROR)
node = {}
registration_url = ''


def register_shutdown():
    """
    Unregister Bambino on shutdown.
    """
    try:
        payload = {'node': json.dumps(node), 'action': 'unregister'}
        requests.post(registration_url, data=payload)
    except requests.exceptions.ConnectionError as e:
        log.error(e.message)


def register_this_bambino():
    """
    Register this nodes data, i.e.
    {
    'name':value,
    'site':value,
    'url':value
    }
    """
    try:
        payload = {'node': json.dumps(node), 'action': 'register'}
        requests.post(registration_url, data=payload)
    except requests.exceptions.ConnectionError as e:
        log.error(e.message)


def register_bambino(n, url, interval):
    """
    Start the Bambino heart beat to let Doula know that
    this node is alive.
    """
    global node
    node = n
    global registration_url
    registration_url = url

    sched = Scheduler()
    sched.start()
    sched.add_interval_job(register_this_bambino, seconds=int(interval))

    # Observe the death of this application
    signal(SIGTERM, lambda signum, stack_frame: exit(1))
    signal(SIGINT, lambda signum, stack_frame: exit(1))
    signal(SIGHUP, lambda signum, stack_frame: exit(1))
    atexit.register(register_shutdown)
