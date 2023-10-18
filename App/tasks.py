from django.conf import settings

from celery import shared_task

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from crawler.spiders.bookmark import BookmarkSpider



@shared_task
def scrapy_runner(bookmarks):
    process = CrawlerProcess(settings=get_project_settings())
    process.crawl(BookmarkSpider, bookmarks)
    process.start()
