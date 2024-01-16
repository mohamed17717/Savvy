import scrapy

from crawler.items import BookmarkItemLoader

# from django.db.models import Count
# from crawler.orm import django_wrapper
# from App import tasks


class BookmarkSpider(scrapy.Spider):
    name = "bookmark"

    def __init__(self, bookmarks: list):
        # self.urls = urls
        self.bookmarks = bookmarks

        from crawler.orm import DjangoProxy
        self.dj_proxy = DjangoProxy()

    def start_requests(self):
        # for url in self.urls:
        for bookmark in self.bookmarks:
            payload = {'bookmark': bookmark}
            yield scrapy.Request(
                bookmark.url, callback=self.parse, cb_kwargs=payload, meta=payload
            )

    def __get_headers(self, response):
        def extract_headers(hx):
            return {hx: response.xpath(f'//{hx}//text()').extract()}

        headers = map(lambda i: f'h{i}', range(1, 6+1))
        headers = map(extract_headers, headers)
        headers_dict = {}
        for h in headers:
            headers_dict.update(h)
        return headers_dict

    def parse(self, response, bookmark):
        bookmark_item_loader = BookmarkItemLoader(response=response)

        # remove all style tags because if there is a style tag inside body, will decrease accuracy
        response.xpath('//style').drop()

        meta_tags = [meta.attrib for meta in response.xpath('//head/meta')]
        page_title = response.xpath('//head/title/text()').extract_first()
        url = response.url
        headers = self.__get_headers(response)

        bookmark_item_loader.add_value('meta_tags', meta_tags)
        bookmark_item_loader.add_value('page_title', page_title)
        bookmark_item_loader.add_value('url', url)
        bookmark_item_loader.add_value('headers', headers)
        bookmark_item_loader.add_value('bookmark', bookmark)

        yield bookmark_item_loader.load_item()

    async def closed(self, reason):
        # TODO delete all of this
        # bookmark_file = await self.dj_proxy.bookmark_parent(self.bookmarks)
        # is_part_of_file = bookmark_file is not None

        # TODO change checking using the tasks list and make a counter in the redis
        # that track how many spider running -> increased on open and decreased on close
        # and check if the counter is 0 to run the clustering process
        # because the current way will be corrupted when i run the spider
        # process by popen instead of run because celery will be no longer aware of spider life
        # and this will make receive spider command a lot faster and more spiders will run in parallel
        # NOTE right now celery worker wait the spider to finish before running the next one

        # TODO when you change the task track and make it depend on redis also
        # make sure to make success rate of crawling is 100%
        # as you store in redis how many time this bookmark tried to crawl

        # if is_part_of_file:
        #     is_related_spiders_finished = await django_wrapper(lambda: bookmark_file.is_tasks_done)
        #     if is_related_spiders_finished:
        #         # avoid failed and not found bookmarks
        #         bookmarks = await django_wrapper(lambda: list(bookmark_file.bookmarks.filter(scrapes__status_code=200).distinct()))
        #         await django_wrapper(tasks.cluster_bookmarks_task.apply_async, kwargs={'bookmarks': bookmarks})
        #     else:
        #         # crawl failed bookmarks to make sure success rate is the high as you can
        #         failed_crawling = await django_wrapper(lambda: list(bookmark_file.bookmarks.annotate(count=Count('scrapes')).filter(crawled=False, count__gt=0, count__lt=5).values_list('id', flat=True)))
        #         await django_wrapper(tasks.batch_bookmarks_to_crawl_task.apply_async, kwargs={'parent': bookmark_file, 'bookmark_ids': failed_crawling})

        # else:
        #     await django_wrapper(tasks.cluster_bookmarks_task.apply_async, kwargs={'bookmarks': self.bookmarks})
        pass
