import json
import subprocess

from celery import shared_task
from celery import current_app
from celery.signals import after_task_publish


@after_task_publish.connect
def update_sent_state(sender=None, headers=None, **kwargs):
    # the task may not exist if sent using `send_task` which
    # sends tasks by name, so fall back to the default result backend
    # if that is the case.
    task = current_app.tasks.get(sender)
    backend = task.backend if task else current_app.backend
 
    backend.store_result(headers['id'], None, "SENT")


@shared_task(queue='scrapy')
def crawl_bookmarks_task(bookmark_ids: list[int]):
    command = ['python', 'manage.py', 'crawl_bookmarks', json.dumps(bookmark_ids)]

    try:
        result = subprocess.run(
            command, capture_output=True, text=True, check=True
        )
        # TODO log the prints
        print("Command output:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("Command failed with error:", e)
        
    return True
