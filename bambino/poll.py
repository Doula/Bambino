from apscheduler.scheduler import Scheduler
import json
import time
import logging
import requests
import sys

module = sys.modules[__name__]
log = logging.getLogger('bambino')
sched = Scheduler()
node = { }
registration_url = ''

def start_heartbeat(n, url):
    """
    Start the Bambino heart beat to let Doula know that
    this node is alive.
    """
    setattr(module, 'node', n)
    setattr(module, 'registration_url', url)
    
    sched.start()

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
        payload = { 'node': json.dumps(node) }
        requests.post(registration_url, data=payload)
    except requests.exceptions.ConnectionError as e:
        log.error(e.message)

    