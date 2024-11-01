from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from App import models, tasks
from realtime.common.redis_utils import RedisPubSub


@receiver(post_save, sender=models.BookmarkFile)
def on_create_bookmark_file_extract_urls(sender, instance, created, **kwargs):
    if not created:
        return

    def event():
        tasks.store_bookmarks_task.delay(instance.id)

        RedisPubSub.pub(
            {
                "type": RedisPubSub.MessageTypes.INIT_UPLOAD,
                "user_id": instance.user.id,
            }
        )

    transaction.on_commit(event)


@receiver(pre_save, sender=models.BookmarkFile)
def on_save_bookmark_file_validate_file_content(sender, instance, **kwargs):
    instance.file_obj.validate()
