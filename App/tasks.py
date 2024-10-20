import json
import logging
import subprocess
import typing

from celery import chord, current_app, shared_task
from celery.result import allow_join_result
from celery.signals import after_task_publish
from django.contrib.auth import get_user_model
from django.contrib.postgres.search import SearchVector
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from App import models
from common.utils.array_utils import window_list
from common.utils.html_utils import extract_image_from_meta
from common.utils.time_utils import fromtimestamp
from realtime.common.redis_utils import RedisPubSub

logger = logging.getLogger(__name__)
User = get_user_model()


def group_bookmarks_by_hook(
    bookmarks, hook_name
) -> list[list[typing.Callable, list[int]]]:
    hooks_methods = {}
    hooks_groups = {}
    for bookmark in bookmarks:
        hook = getattr(bookmark.hooks, hook_name)
        hook_result = hook()
        if hook_result is not None:
            func_name = hook_result.__name__

            hooks_methods[func_name] = hook_result

            hooks_groups.setdefault(func_name, [])
            hooks_groups[func_name].append(bookmark.id)

    # zip methods and groups by name
    return [(method, hooks_groups[name]) for name, method in hooks_methods.items()]


@after_task_publish.connect
def update_sent_state(sender=None, headers=None, **kwargs):
    # the task may not exist if sent using `send_task` which
    # sends tasks by name, so fall back to the default result backend
    # if that is the case.
    task = current_app.tasks.get(sender)
    backend = task.backend if task else current_app.backend

    backend.store_result(headers["id"], None, "SENT")


@shared_task(queue="orm")
def store_bookmarks_task(parent_id: int):
    parent = models.BookmarkFile.objects.get(id=parent_id)
    bookmarks_data = parent.cleaned_bookmarks_links()

    RedisPubSub.pub(
        {
            "type": RedisPubSub.MessageTypes.FILE_UPLOAD,
            "user_id": parent.user.id,
            "total_bookmarks": len(bookmarks_data),
        }
    )

    bookmarks = tuple(map(parent.init_bookmark, bookmarks_data))
    models.Bookmark.objects.bulk_create(bookmarks, batch_size=250)

    # TODO refactor creating website and move it to another task
    domains = {b.domain for b in bookmarks}
    website_objects = [
        models.Website(user=parent.user, domain=domain) for domain in domains
    ]
    models.Website.objects.bulk_create(
        website_objects, batch_size=250, ignore_conflicts=True
    )

    # Add relation between bookmark and website & store favicon to website
    website_relation_map = {
        w.domain: w for w in parent.user.websites.filter(domain__in=domains)
    }
    websites = []
    for b in bookmarks:
        website = website_relation_map[b.domain]
        b.website = website
        website.favicon = b.more_data.get("icon")
        websites.append(website)

    models.Website.objects.bulk_update(websites, ["favicon"], batch_size=250)
    models.Bookmark.objects.bulk_update(bookmarks, ["website"], batch_size=250)

    batch_bookmarks_to_tasks.delay([b.id for b in bookmarks])

    return f"BookmarkFile<{parent_id}> [Created] {len(bookmarks_data)} Bookmarks"


@shared_task(queue="orm")
def batch_bookmarks_to_tasks(bookmark_ids: list[int]):
    batch_size = 30

    bookmarks = models.Bookmark.objects.filter(id__in=bookmark_ids)
    batches = group_bookmarks_by_hook(bookmarks, "get_batch_method")

    tasks = []
    for hook_method, hook_group in batches:
        id_groups = window_list(hook_group, batch_size)
        tasks.extend([hook_method.s(group) for group in id_groups])

    callback = post_batch_bookmarks_task.s(bookmark_ids=bookmark_ids).set(queue="orm")

    job = chord(tasks)(callback)
    with allow_join_result():
        job.get()

    return f"[Batched ({len(bookmark_ids)})] {bookmark_ids}"


@shared_task(queue="scrapy")
def crawl_bookmarks_task(bookmark_ids: list[int]):
    models.Bookmark.objects.filter(id__in=bookmark_ids).start_crawl()

    ids = json.dumps(bookmark_ids)
    command = ["python", "manage.py", "crawl_bookmarks", ids]
    subprocess.run(command, capture_output=True, text=True, check=True)

    return f"[Crawled ({len(bookmark_ids)})] {bookmark_ids}"


@shared_task(queue="orm")
def store_webpage_task(bookmark_id, page_title, meta_tags, headers):
    with transaction.atomic():
        bookmark = models.Bookmark.objects.get(id=bookmark_id)
        # TODO make title way shorter
        webpage = models.BookmarkWebpage.objects.create(
            bookmark=bookmark, title=page_title[:2048]
        )
        models.WebpageMetaTag.bulk_create(webpage, meta_tags)
        models.WebpageHeader.bulk_create(webpage, headers)

    store_bookmark_image_task.delay(bookmark_id, meta_tags)
    return f"[StoreWebpage] Bookmark<{bookmark_id}> Meta<{len(meta_tags)}> Header<{len(headers)}>"  # noqa


@shared_task(queue="orm")
def deep_clone_bookmarks_task(bookmark_ids, user_id, file_id, more_data=None):
    if more_data is None:
        more_data = []
    bookmarks_file = models.BookmarkFile.objects.get(id=file_id)
    bookmarks = models.Bookmark.objects.filter(id__in=bookmark_ids)
    user = User.objects.get(pk=user_id)

    id_to_more_data = dict(zip(bookmark_ids, more_data))
    # TODO This is make too much operations in database so bulk doing them
    for bookmark in bookmarks:
        data = id_to_more_data[bookmark.id]
        added_at = data.pop("added_at", None)
        if added_at:
            added_at = fromtimestamp(added_at)

        bookmark.deep_clone(user, bookmarks_file, added_at=added_at)

    return f"[DeepClone ({len(bookmark_ids)})] {bookmark_ids}"


@shared_task(queue="download_images")
def store_bookmark_image_task(bookmark_id, meta_tags=None, image_url=None):
    bookmark = models.Bookmark.objects.get(id=bookmark_id)
    if meta_tags:
        image_url = extract_image_from_meta(meta_tags)

    if image_url:
        try:
            bookmark.set_image_from_url(image_url)
        except Exception as e:
            logger.error(f"store_bookmark_image_task({bookmark_id}, {image_url})")
            raise e

    return f"[StoreImage] Bookmark<{bookmark_id}>"


@shared_task(queue="download_images")
def schedule_store_bookmark_image_task(bookmark_id, image_url):
    wait_time = 60 * 60  # 1 hour
    store_bookmark_image_task.apply_async(
        kwargs={"bookmark_id": bookmark_id, "image_url": image_url}, countdown=wait_time
    )

    return f"[ScheduleStoreImage] Bookmark<{bookmark_id}>"


@shared_task(queue="orm")
def store_bookmark_file_analytics_task(parent_id):
    parent = models.BookmarkFile.objects.get(id=parent_id)

    parent.total_links_count = parent.bookmarks.count()
    parent.succeeded_links_count = parent.bookmarks.filter(
        Q(
            process_status=models.Bookmark.ProcessStatus.CLONED.value,
        )
        | Q(process_status__gte=models.Bookmark.ProcessStatus.CRAWLED.value)
    ).count()
    parent.failed_links_count = parent.total_links_count - parent.succeeded_links_count
    parent.save()

    return f"StoreFileAnalytics<{parent_id}>"


@shared_task(queue="orm")
def index_search_vector_task(bookmark_ids):
    from App import views

    search_fields = views.BookmarkAPI.search_fields
    bookmarks = models.Bookmark.objects.filter(id__in=bookmark_ids).annotate(
        inline_search_vector=SearchVector(*search_fields)
    )
    for bm in bookmarks:
        bm.search_vector = bm.inline_search_vector

    models.Bookmark.objects.bulk_update(bookmarks, ["search_vector"], batch_size=250)

    return f"[IndexedSearchVector ({len(bookmark_ids)})] {bookmark_ids}"


@shared_task(queue="orm")
def post_batch_bookmarks_task(callback_result=[], bookmark_ids=[]):
    if not bookmark_ids:
        return

    bookmarks = models.Bookmark.objects.filter(id__in=bookmark_ids)
    batches = group_bookmarks_by_hook(bookmarks, "post_batch")

    for hook_method, hook_group in batches:
        hook_method(hook_group)

    bookmarks.crawled()

    parent = models.Bookmark.objects.get(id=bookmark_ids[0]).parent_file
    user_id = parent.user.id

    store_bookmark_file_analytics_task.delay(parent.id)
    cluster_checker_task.delay(user_id=user_id, bookmark_ids=bookmark_ids)

    return f"[PostBatched ({len(bookmark_ids)})] {bookmark_ids}"


@shared_task(queue="orm")
def cluster_checker_task(callback_result=None, user_id=None, bookmark_ids=None):
    # TODO not important just rewrite the logic again
    if callback_result is None:
        callback_result = []
    if bookmark_ids is None:
        bookmark_ids = []

    index_search_vector_task.apply_async(kwargs={"bookmark_ids": bookmark_ids})

    return f"[ClusterChecker] (succeed) Bookmarks<{len(bookmark_ids)}> {bookmark_ids}"


@shared_task(queue="orm")
def delete_bookmarks_beat_task():
    today = timezone.now().date()
    bookmarks = models.Bookmark.hidden_objects.filter(
        delete_scheduled_at__date__lte=today
    )
    bookmarks.delete()

    return f"[DeleteBookmarks {today}] ({len(bookmarks)})"
