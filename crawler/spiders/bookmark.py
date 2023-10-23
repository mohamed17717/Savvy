import scrapy

from crawler.items import BookmarkItemLoader


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
        await self.dj_proxy.cluster_bookmarks(self.bookmarks)
