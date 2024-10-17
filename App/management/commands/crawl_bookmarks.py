import json

from django.core.management.base import BaseCommand
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from App import models
from crawler.spiders.bookmark import BookmarkSpider


class Command(BaseCommand):
    help = "Crawl bookmarks using Scrapy"

    def add_arguments(self, parser):
        parser.add_argument(
            "bookmarks", type=json.loads, help="List of IDs of bookmarks to scrape"
        )

        # Options
        parser.add_argument("--urls", nargs="+", type=str, help="URLs to scrape")

    def handle(self, *args, **kwargs):
        bookmarks = models.Bookmark.objects.filter(pk__in=kwargs["bookmarks"])
        if bookmarks.exists() is False:
            return

        process = CrawlerProcess(settings=get_project_settings())
        process.crawl(BookmarkSpider, list(bookmarks))
        process.start()
