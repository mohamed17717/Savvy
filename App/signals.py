from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from crawler.spiders.bookmark import BookmarkSpider

from App import models


@receiver(post_save, sender=models.BookmarkFile)
def on_create_bookmark_file_extract_urls(sender, instance, created, **kwargs):
    if created is False:
        return

    bookmarks = [
        models.Bookmark.instance_by_parent(instance, bookmark)
        for bookmark in instance.bookmarks_links
    ]
    # models.Bookmark.objects.bulk_create(bookmarks)

    # run them in background celery task
    # urls = [bookmark['url'] for bookmark in instance.bookmarks]
    # process = CrawlerProcess(settings=get_project_settings())
    # process.crawl(BookmarkSpider, urls=urls)
    # process.start()


@receiver(pre_save, sender=models.BookmarkFile)
def on_save_bookmark_file_validate_file_content(sender, instance, **kwargs):
    instance.file_obj.validate(raise_exception=True)


@receiver(post_save, sender=models.DocumentCluster)
def on_create_cluster_start_labeling(sender, instance, created, **kwargs):
    if not created:
        return

    general_vector = instance.general_words_vector

    # sort words desc on its general weight
    words = sorted(general_vector.keys(), key=lambda i: -general_vector[i])

    # 2/3 of words consider tops but less than 10
    MAX_WORDS_COUNT = 10
    top_words_count = len(words) * 2 // 3
    top_words_count = min(MAX_WORDS_COUNT, top_words_count)
    top_words = words[:top_words_count]

    # store labels
    models.ClusterTag.objects.bulk_create([
        models.ClusterTag(cluster=instance, name=word)
        for word in top_words
    ])
