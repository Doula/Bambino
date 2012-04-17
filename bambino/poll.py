from apscheduler.scheduler import Scheduler
import json
import time
import logging
import requests

log = logging.getLogger('bambino')
sched = Scheduler()

def start_heartbeat(n, url):
    # alextodo, figure out if there is a better way to configure this
    # global looks kinda ugly. just saying. set module variables probably
    node = n
    global node
    reg_url = url
    global reg_url
    
    sched.start()

@sched.interval_schedule(seconds=5)
def job_function():
    try:
        print "Registering node",time.time()
        print json.dumps(node)
        print reg_url
        
        payload = {'node': json.dumps(node)}
        requests.post(reg_url, data=payload)
    except requests.exceptions.ConnectionError as e:
        log.error(e.message)

    