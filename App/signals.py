import redis
import json

from django.db import transaction
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from dj.settings import REDIS_HOST, REDIS_PORT
from App import models, tasks


class BookmarkRedisPublisher:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

    class Types:
        FILE_UPLOAD = 1
        BOOKMARK_CHANGE = 2

    def __init__(self, user):
        self.user = user
        self.CHANNEL_NAME = 'bookmarks_progress'

    def publish(self, data):
        _type = self.Types.FILE_UPLOAD
        if 'bookmark_id' in data.keys():
            _type = self.Types.BOOKMARK_CHANGE

        payload = {
            'user_id': self.user.id,
            'type': _type,
            'data': data
        }
        self.redis_client.publish(self.CHANNEL_NAME, json.dumps(payload))


@receiver(post_save, sender=models.BookmarkFile)
def on_create_bookmark_file_extract_urls(sender, instance, created, **kwargs):
    if not created:
        return

    def event():
        links = instance.bookmarks_links
        tasks.store_bookmarks_task.delay(instance.id, links)

        publisher = BookmarkRedisPublisher(instance.user)
        publisher.publish({'total_bookmarks': len(links)})

    transaction.on_commit(event)


@receiver(pre_save, sender=models.BookmarkFile)
def on_save_bookmark_file_validate_file_content(sender, instance, **kwargs):
    instance.file_obj.validate(raise_exception=True)


@receiver(pre_save, sender=models.Bookmark)
def on_change_bookmark_process_status(sender, instance, **kwargs):
    updated = instance.pk is not None
    if not updated:
        return

    old_instance = sender.objects.get(pk=instance.pk)
    process_status_changed = old_instance.process_status != instance.process_status

    if not process_status_changed:
        return

    status_go_bad_direction = instance.process_status < old_instance.process_status
    if status_go_bad_direction:
        raise ValueError('Cannot go to lower status')

    # Tell redis about this change
    publisher = BookmarkRedisPublisher(instance.user)
    publisher.publish(
        {'bookmark_id': instance.id, 'status': instance.process_status}
    )
