import json
import subprocess

from celery import shared_task


@shared_task(queue='scrapy')
def crawl_bookmarks_task(bookmarks):
    ids = json.dumps([bm.id for bm in bookmarks])
    command = ['python', 'manage.py', 'crawl_bookmarks', ids]

    try:
        result = subprocess.run(
            command, capture_output=True, text=True, check=True
        )
        # TODO log the prints
        print("Command output:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("Command failed with error:", e)
