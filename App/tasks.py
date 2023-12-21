import json
import os
import subprocess
from functools import partial

from django.db import transaction

from celery import shared_task
from celery import current_app
from celery.signals import after_task_publish

from App import models


@after_task_publish.connect
def update_sent_state(sender=None, headers=None, **kwargs):
    # the task may not exist if sent using `send_task` which
    # sends tasks by name, so fall back to the default result backend
    # if that is the case.
    task = current_app.tasks.get(sender)
    backend = task.backend if task else current_app.backend

    backend.store_result(headers['id'], None, "SENT")


@shared_task(queue='orm')
def store_bookmarks_task(parent: 'models.BookmarkFile', bookmarks: list[dict]):
    Bookmark_Creator = partial(models.Bookmark.instance_by_parent, parent)
    bookmarks = map(Bookmark_Creator, bookmarks)
    bookmarks = list(bookmarks)

    # TODO add batch size or batch the data in the task
    models.Bookmark.objects.bulk_create(bookmarks, batch_size=250)

    # batch ids in batches of 30
    bookmark_ids = [bm.id for bm in bookmarks]
    batch_size = 30
    steps = range(0, len(bookmark_ids), batch_size)
    sliced_ids = [bookmark_ids[i:i + batch_size] for i in steps]
    for ids in sliced_ids:
        task = crawl_bookmarks_task.apply_async(
            kwargs={'bookmark_ids': ids})

        parent.tasks.append(task.task_id)
        parent.save()


@shared_task(queue='scrapy')
def crawl_bookmarks_task(bookmark_ids: list[int]):
    # make scrapy aware we inside a test env
    testing_args = []
    is_test_mode = bool(os.getenv("DJANGO_TEST_MODE"))
    if is_test_mode:
        testing_args = ['--settings', 'dj.settings.settings_test']

    command = [
        'python', 'manage.py', 'crawl_bookmarks',
        json.dumps(bookmark_ids), *testing_args
    ]
    subprocess.run(command, capture_output=True, text=True, check=True)

    return True


@shared_task(queue='orm')
def store_webpage_task(bookmark, url, page_title, meta_tags, headers):
    with transaction.atomic():
        webpage = models.BookmarkWebpage.objects.create(
            bookmark=bookmark, url=url, title=page_title
        )

        models.WebpageMetaTag.bulk_create(webpage, meta_tags)
        models.WebpageHeader.bulk_create(webpage, headers)


@shared_task(queue='orm')
def store_weights_task(bookmark):
    bookmark.store_word_vector()
    bookmark.store_tags()


@shared_task(queue='orm')
def cluster_bookmarks_task(bookmarks):
    models.Bookmark.cluster_bookmarks(bookmarks)
