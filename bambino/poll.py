from apscheduler.scheduler import Scheduler
import time

sched = Scheduler()

def start_heartbeat():
    sched.start()

@sched.interval_schedule(seconds=60)
def job_function():
    print "update doula, ",time.time()

    