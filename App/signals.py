from django.db import transaction
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from App import models, tasks

from realtime.common.redis_utils import RedisPubSub


@receiver(post_save, sender=models.BookmarkFile)
def on_create_bookmark_file_extract_urls(sender, instance, created, **kwargs):
    if not created:
        return

    def event():
        links = instance.cleaned_bookmarks_links()
        tasks.store_bookmarks_task.delay(instance.id, links)

        RedisPubSub.pub({
            'type': RedisPubSub.MessageTypes.FILE_UPLOAD,
            'user_id': instance.user.id,
            'total_bookmarks': len(links),
        })

    transaction.on_commit(event)


@receiver(pre_save, sender=models.BookmarkFile)
def on_save_bookmark_file_validate_file_content(sender, instance, **kwargs):
    instance.file_obj.validate(raise_exception=True)
