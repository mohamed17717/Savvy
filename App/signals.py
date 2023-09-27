from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from scrapy.crawler import CrawlerProcess
from symbiotes.symbiotes.spiders.venom import VenomSpider

from App import models


@receiver(post_save, sender=models.BookmarkFile)
def on_create_bookmark_file_extract_urls(sender, instance: models.BookmarkFile, created, **kwargs):
    if created is False:
        return

    bookmarks = [
        models.Bookmark.instance_by_parent(instance, bookmark)
        for bookmark in instance.bookmarks
    ]
    models.Bookmark.objects.bulk_create(bookmarks)

    # TODO: give command to scrapy to start the spider
    # also run them in background celery task
    # process = CrawlerProcess()
    # process.crawl(VenomSpider, urls)
    # process.start()


@receiver(pre_save, sender=models.BookmarkFile)
def on_save_bookmark_file_validate_file_content(sender, instance: models.BookmarkFile, created, **kwargs):
    instance.file_obj.validate(raise_exception=True)