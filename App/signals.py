from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from App import models, tasks


@receiver(post_save, sender=models.BookmarkFile)
def on_create_bookmark_file_extract_urls(sender, instance, created, **kwargs):
    # TODO make location is not editable
    if created:
        tasks.store_bookmarks_task.apply_async(kwargs={
            'parent': instance, 'bookmarks': instance.bookmarks_links
        })


@receiver(pre_save, sender=models.BookmarkFile)
def on_save_bookmark_file_validate_file_content(sender, instance, **kwargs):
    instance.file_obj.validate(raise_exception=True)


@receiver(post_save, sender=models.ScrapyResponseLog)
def on_create_scrapy_log_make_bookmark_crawled(sender, instance, created, **kwargs):
    bm = instance.bookmark

    if created and bm is not None:
        bm.crawled = instance.status_code in [200, 404]
        bm.save(update_fields=['crawled'])
