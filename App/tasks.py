import json
import subprocess

from django.db import transaction

from celery import shared_task, current_app, chord
from celery.signals import after_task_publish
from celery.result import allow_join_result

from App import models
from common.utils.array_utils import window_list


@after_task_publish.connect
def update_sent_state(sender=None, headers=None, **kwargs):
    # the task may not exist if sent using `send_task` which
    # sends tasks by name, so fall back to the default result backend
    # if that is the case.
    task = current_app.tasks.get(sender)
    backend = task.backend if task else current_app.backend

    backend.store_result(headers['id'], None, "SENT")


@shared_task(queue='orm')
def store_bookmarks_task(parent_id: int, bookmarks_data: list[dict]):
    parent = models.BookmarkFile.objects.get(id=parent_id)

    bookmarks = [parent.init_bookmark(item) for item in bookmarks_data]
    del bookmarks_data

    models.Bookmark.objects.bulk_create(bookmarks, batch_size=250)
    batch_bookmarks_to_crawl_task.delay([bm.id for bm in bookmarks])


@shared_task(queue='orm', ignore_result=True)
def batch_bookmarks_to_crawl_task(bookmark_ids: list[int]):
    batch_size = 30
    id_groups = window_list(bookmark_ids, batch_size, batch_size)

    tasks = (crawl_bookmarks_task.s(group) for group in id_groups)
    callback = cluster_checker_task.s(bookmark_ids=bookmark_ids, iteration=0)
    job = chord(tasks)(callback)
    with allow_join_result():
        job.get()


@shared_task(queue='scrapy')
def crawl_bookmarks_task(bookmark_ids: list[int]):
    ids = json.dumps(bookmark_ids)
    command = ['python', 'manage.py', 'crawl_bookmarks', ids]
    subprocess.run(command, capture_output=True, text=True, check=True)


@shared_task(queue='orm')
def store_webpage_task(bookmark_id, url, page_title, meta_tags, headers):
    with transaction.atomic():
        bookmark = models.Bookmark.objects.get(id=bookmark_id)
        webpage = models.BookmarkWebpage.objects.create(
            bookmark=bookmark, url=url, title=page_title[:2048]
        )

        models.WebpageMetaTag.bulk_create(webpage, meta_tags)
        models.WebpageHeader.bulk_create(webpage, headers)


@shared_task(queue='orm')
def store_weights_task(bookmark_id):
    bookmark = models.Bookmark.objects.get(id=bookmark_id)
    bookmark.store_word_vector()
    bookmark.store_tags()


@shared_task(queue='orm')
def cluster_bookmarks_task(bookmark_ids):
    bookmarks = models.Bookmark.objects.filter(id__in=bookmark_ids)
    models.Bookmark.cluster_bookmarks(bookmarks)


@shared_task(queue='orm')
def cluster_checker_task(callback_result=[], bookmark_ids=[], iteration=0):
    max_time = 15*60  # 15 min
    wait_time = 10  # 10 sec
    max_iteration = max_time // wait_time

    uncompleted_bookmarks = models.Bookmark.objects.filter(
        id__in=bookmark_ids, crawled=True, words_weights__isnull=True
    ).exists()
    accepted = any([
        iteration >= max_iteration,
        uncompleted_bookmarks is False
    ])

    if accepted:
        cluster_bookmarks_task.apply_async(
            kwargs={'bookmark_ids': bookmark_ids})
    else:
        cluster_checker_task.apply_async(
            kwargs={'bookmark_ids': bookmark_ids, 'iteration': iteration+1}, countdown=wait_time)
