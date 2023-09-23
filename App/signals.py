import json

from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from App import models


@receiver(post_save, sender=models.BookmarkFile)
def on_create_bookmark_file_extract_urls(sender, instance:models.BookmarkFile, created, **kwargs):
    if created is False: return

    # NOTE: THIS IS PSEUDO CODE
    src = instance.file_content
    if instance.is_html:
        urls = []
    elif instance.is_json:
        urls = json.loads(src)

    for url in urls:
        models.Bookmark(url=url)
    
    # >>> give command to scrapy to start the spider
    # there is new urls come here
    # also run them in background celery task



@receiver(pre_save, sender=models.BookmarkFile)
def on_save_bookmark_file_validate_file_content(sender, instance:models.BookmarkFile, created, **kwargs):
    if instance.is_html:
        # validate it contain urls and is a real bookmark file
        ...
    elif instance.is_json:
        # is an array of urls
        ...
