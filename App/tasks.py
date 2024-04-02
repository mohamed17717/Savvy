import json
import subprocess
import logging

from django.db import transaction
from django.db.models import Q
from django.contrib.auth import get_user_model

from celery import shared_task, current_app, chord
from celery.signals import after_task_publish
from celery.result import allow_join_result

from App import models

from common.utils.array_utils import window_list
from common.utils.html_utils import extract_image_from_meta


logger = logging.getLogger(__name__)
User = get_user_model()


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

    # Start creating new bookmarks
    bookmarks = tuple(map(parent.init_bookmark, bookmarks_data))

    models.Bookmark.objects.bulk_create(bookmarks, batch_size=250)
    batch_bookmarks_to_crawl_task.delay(
        [bookmark.id for bookmark in bookmarks])


@shared_task(queue='orm')
def batch_bookmarks_to_crawl_task(bookmark_ids: list[int]):
    batch_size = 30
    id_groups = window_list(bookmark_ids, batch_size, batch_size)

    tasks = [
        crawl_bookmarks_task.s(group).set(queue='scrapy')
        for group in id_groups
    ]
    callback = (
        on_finish_crawling_task.s(bookmark_ids=bookmark_ids).set(queue='orm')
    )
    job = chord(tasks)(callback)
    with allow_join_result():
        job.get()


@shared_task(queue='scrapy')
def crawl_bookmarks_task(bookmark_ids: list[int]):
    models.Bookmark.objects.filter(id__in=bookmark_ids).update_process_status(
        models.Bookmark.ProcessStatus.START_CRAWL.value
    )

    ids = json.dumps(bookmark_ids)
    command = ['python', 'manage.py', 'crawl_bookmarks', ids]
    subprocess.run(command, capture_output=True, text=True, check=True)


@shared_task(queue='orm')
def store_webpage_task(bookmark_id, page_title, meta_tags, headers):
    with transaction.atomic():
        bookmark = models.Bookmark.objects.get(id=bookmark_id)
        webpage = models.BookmarkWebpage.objects.create(
            bookmark=bookmark, title=page_title[:2048]
        )

        store_bookmark_image_task.delay(bookmark_id, meta_tags)
        models.WebpageMetaTag.bulk_create(webpage, meta_tags)
        models.WebpageHeader.bulk_create(webpage, headers)


@shared_task(queue='orm')
def store_bookmark_image_task(bookmark_id, meta_tags):
    bookmark = models.Bookmark.objects.get(id=bookmark_id)
    image_url = extract_image_from_meta(meta_tags)
    if image_url:
        try:
            bookmark.set_image_from_url(image_url)
        except Exception as e:
            logger.error('store_bookmark_image_task(%s, %s)' %
                         (bookmark_id, image_url))
            raise e


@shared_task(queue='orm')
def store_weights_task(bookmark_id):
    Status = models.Bookmark.ProcessStatus

    with transaction.atomic():
        bookmark = models.Bookmark.objects.filter(
            id=bookmark_id,
            words_weights__isnull=True,
            # process_status__lt=Status.START_TEXT_PROCESSING.value
        ).first()
        if bookmark:
            bookmark.update_process_status(Status.START_TEXT_PROCESSING.value)

            bookmark.store_word_vector()
            bookmark.store_tags()

            bookmark.update_process_status(Status.TEXT_PROCESSED.value)


@shared_task(queue='orm')
def cluster_bookmarks_task(user_id):
    user = User.objects.get(pk=user_id)
    models.Bookmark.make_clusters(user)


@shared_task(queue='orm')
def store_bookmark_file_analytics_task(parent_id):
    parent = models.BookmarkFile.objects.get(id=parent_id)

    parent.total_links_count = parent.bookmarks.count()
    parent.succeeded_links_count = parent.bookmarks.filter(
        Q(process_status=models.Bookmark.ProcessStatus.CLONED.value,)
        | Q(process_status__gte=models.Bookmark.ProcessStatus.CRAWLED.value)
    ).count()
    parent.failed_links_count = parent.total_links_count - parent.succeeded_links_count
    parent.save()


@shared_task(queue='orm')
def on_finish_crawling_task(callback_result=[], bookmark_ids=[]):
    if not bookmark_ids:
        return

    models.Bookmark.objects.filter(id__in=bookmark_ids).update_process_status(
        models.Bookmark.ProcessStatus.CRAWLED.value)

    parent = models.Bookmark.objects.get(id=bookmark_ids[0]).parent_file
    user_id = parent.user.id

    store_bookmark_file_analytics_task.delay(parent.id)
    cluster_checker_task.delay(user_id, bookmark_ids, 0)


@shared_task(queue='orm')
def cluster_checker_task(user_id, bookmark_ids=[], iteration=0):
    max_time = 10*60  # 10 min
    wait_time = 2  # 2 sec
    max_iteration = max_time // wait_time

    uncompleted_bookmarks = models.Bookmark.objects.filter(
        id__in=bookmark_ids,
        words_weights__isnull=True
    ).exists()
    accepted = any([
        iteration >= max_iteration,
        uncompleted_bookmarks is False
    ])

    if accepted:
        models.Bookmark.objects.filter(id__in=bookmark_ids).update_process_status(
            models.Bookmark.ProcessStatus.START_CLUSTER.value)
        cluster_bookmarks_task.apply_async(
            kwargs={'user_id': user_id})
    else:
        cluster_checker_task.apply_async(
            kwargs={'user_id': user_id, 'bookmark_ids': bookmark_ids, 'iteration': iteration+1}, countdown=wait_time)
