import scrapy
from crawler.items import BookmarkItemLoader


class BookmarkSpider(scrapy.Spider):
    name = "bookmark"
    
    def __init__(self, bookmarks: list): #: list[str]):
        # self.urls = urls
        self.bookmarks = bookmarks

    def start_requests(self):
        # for url in self.urls:
        print('\n\n', self.bookmarks, '\n\n')
        for bookmark in self.bookmarks:
            self.bookmark = bookmark
            url = bookmark.url
            domain = url.split('://')[1].split('/')[0]
            self.allowed_domains = [domain]
            yield scrapy.Request(url, callback=self.parse)

    def __get_headers(self, response):
        def extract_headers(hx):
            return {hx: response.xpath(f'//{hx}//text()').extract()}

        headers = map(lambda i: f'h{i}', range(1, 6+1))
        headers = map(extract_headers, headers)
        headers_dict = {}
        for h in headers:
            headers_dict.update(h)

    def parse(self, response):
        bookmark_item_loader = BookmarkItemLoader(response=response)

        meta_tags = [meta.attrib for meta in response.xpath('//head/meta')]
        page_title = response.xpath('//head/title/text()').extract_first()
        url = response.url
        headers = self.__get_headers(response)

        bookmark_item_loader.add_value('meta_tags', meta_tags)
        bookmark_item_loader.add_value('page_title', page_title)
        bookmark_item_loader.add_value('url', url)
        bookmark_item_loader.add_value('headers', headers)

        yield bookmark_item_loader.load_item()
