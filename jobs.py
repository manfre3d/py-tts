import queue
import uuid

_jobs = {}


def create_job():
    job_id = str(uuid.uuid4())
    _jobs[job_id] = queue.Queue()
    return job_id


def push(job_id, event):
    if job_id in _jobs:
        _jobs[job_id].put(event)


def get_queue(job_id):
    return _jobs.get(job_id)


def cleanup(job_id):
    _jobs.pop(job_id, None)
