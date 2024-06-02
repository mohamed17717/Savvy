from django.db import transaction
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from App import models, tasks


@receiver(post_save, sender=models.BookmarkFile)
def on_create_bookmark_file_extract_urls(sender, instance, created, **kwargs):
    if not created:
        return

    transaction.on_commit(
        lambda: tasks.store_bookmarks_task.delay(instance.id))


@receiver(pre_save, sender=models.BookmarkFile)
def on_save_bookmark_file_validate_file_content(sender, instance, **kwargs):
    instance.file_obj.validate()
