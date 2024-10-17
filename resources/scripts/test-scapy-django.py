from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from App.models import Bookmark
from crawler.spiders.bookmark import BookmarkSpider

bookmarks = list(Bookmark.objects.all())

process = CrawlerProcess(settings=get_project_settings())
process.crawl(BookmarkSpider, bookmarks=bookmarks)
process.start()
