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

    # categorize bookmarks to route them to the right flow controller
    categories = {}  # type: dict[str, list[models.Bookmark]]
    flow_controllers = {}  # type: dict[str, models.FlowController]
    for bookmark in bookmarks:
        if bookmark.flow_controller:
            domain = bookmark.flow_controller.DOMAIN

            categories.setdefault(domain, [])
            categories[domain].append(bookmark)
            flow_controllers[domain] = bookmark.flow_controller

    for domain, domain_bookmarks in categories.items():
        controller = flow_controllers[domain]
        controller(domain_bookmarks).run_flow()
    # batch bookmarks that don't have custom flow controller
    bookmarks = list(filter(lambda b: not b.flow_controller, bookmarks))
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


@shared_task(queue='orm')
def batch_bookmarks_to_crawl_without_callback_task(bookmark_ids: list[int]):
    batch_size = 30
    id_groups = window_list(bookmark_ids, batch_size, batch_size)

    tasks = [
        crawl_bookmarks_task.s(group).set(queue='scrapy')
        for group in id_groups
    ]
    callback = (
        empty_callback_task.s(bookmark_ids=bookmark_ids).set(queue='orm')
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


@shared_task(queue='download_images')
def store_bookmark_image_task(bookmark_id, meta_tags=None, image_url=None):
    bookmark = models.Bookmark.objects.get(id=bookmark_id)
    if meta_tags:
        image_url = extract_image_from_meta(meta_tags)

    if image_url:
        try:
            bookmark.set_image_from_url(image_url)
        except Exception as e:
            logger.error(
                'store_bookmark_image_task(%s, %s)' % (bookmark_id, image_url))
            raise e


@shared_task(queue='download_images')
def schedule_store_bookmark_image_task(bookmark_id, image_url):
    wait_time = 60 * 60  # 1 hour
    store_bookmark_image_task.apply_async(kwargs={
        'bookmark_id': bookmark_id,
        'image_url': image_url
    }, countdown=wait_time)


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
            bookmark.update_process_status(Status.TEXT_PROCESSED.value)


@shared_task(queue='orm')
def store_tags_task(user_id):
    user = User.objects.get(pk=user_id)
    bookmark_ids = user.bookmarks.filter(tags__isnull=True).values_list('id', flat=True)
    models.Tag.update_tags_with_new_bookmarks(list(bookmark_ids))


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
def empty_callback_task(callback_result=[], bookmark_ids=[]):
    pass


@shared_task(queue='orm')
def cluster_checker_task(user_id, bookmark_ids=[], iteration=0, uncompleted_bookmarks_history: dict = {}):
    max_time = 3*60  # 3 min
    wait_time = 2  # 2 sec
    max_iteration = max_time // wait_time

    uncompleted_bookmarks = models.Bookmark.objects.filter(
        id__in=set(bookmark_ids) - set(
            [i for i, value in uncompleted_bookmarks_history.items() if value['times'] > 3]),
        words_weights__isnull=True
    )

    for uncompleted in uncompleted_bookmarks:
        uncompleted_bookmarks_history.setdefault(
            uncompleted.id, {'times': 0, 'status': 'wait'})
        uncompleted_bookmarks_history[uncompleted.id]['times'] += 1

    # if this bookmark come more than 3 times
    if uncompleted_bookmarks.exists():
        has_scrapes = uncompleted_bookmarks.filter(
            scrapes__isnull=False).values_list('id', flat=True)
        for bookmark_id in has_scrapes:
            bookmark_history = uncompleted_bookmarks_history[bookmark_id]
            if bookmark_history['status'] != 'wait':
                continue
            elif bookmark_history['times'] == 3:
                bookmark_history['status'] = 'calculated'
                store_weights_task.delay(bookmark_id)

        has_no_scrapes = uncompleted_bookmarks.filter(
            scrapes__isnull=True).values_list('id', flat=True)
        ready_to_scrape = []
        for i, value in uncompleted_bookmarks_history.items():
            if i in has_no_scrapes and value['times'] > 3 and value['status'] == 'wait':
                ready_to_scrape.append(i)
                uncompleted_bookmarks_history[i]['status'] = 'scraped'

        if ready_to_scrape:
            tasks = [crawl_bookmarks_task.s(ready_to_scrape).set(queue='scrapy')]
            callback = (
                cluster_checker_task.s(
                    user_id=user_id, bookmark_ids=bookmark_ids, 
                    iteration=iteration+1, 
                    uncompleted_bookmarks_history=uncompleted_bookmarks_history
                ).set(queue='orm')
            )
            job = chord(tasks)(callback)
            with allow_join_result():
                job.get()

            return

    accepted = any([
        iteration >= max_iteration,
        uncompleted_bookmarks.exists() is False
    ])

    if accepted:
        models.Bookmark.objects.filter(id__in=bookmark_ids).update_process_status(
            models.Bookmark.ProcessStatus.START_CLUSTER.value)
        uncompleted_bookmarks = models.Bookmark.objects.filter(
            user_id=user_id, words_weights__isnull=True
        )
        for bookmark in uncompleted_bookmarks:
            bookmark.store_word_vector()

        store_tags_task.apply_async(kwargs={'user_id': user_id})
        cluster_bookmarks_task.apply_async(kwargs={'user_id': user_id})
    else:
        cluster_checker_task.apply_async(
            kwargs={'user_id': user_id, 'bookmark_ids': bookmark_ids, 'iteration': iteration+1, 'uncompleted_bookmarks_history': uncompleted_bookmarks_history}, countdown=wait_time)
