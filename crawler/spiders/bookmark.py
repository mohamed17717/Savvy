import scrapy


class BookmarkSpider(scrapy.Spider):
    name = "bookmark"

    def __init__(self, bookmarks: list):
        self.bookmarks = bookmarks

    def start_requests(self):
        # for url in self.urls:
        for bookmark in self.bookmarks:
            kwargs = {
                "callback": self.parse,
                "cb_kwargs": {"bookmark": bookmark},
                "meta": {"bookmark": bookmark},
            }
            if cookies := bookmark.hooks.crawler_cookies():
                kwargs["cookies"] = cookies

            yield scrapy.Request(bookmark.url, **kwargs)

    def parse(self, response, bookmark):
        ItemLoader = bookmark.hooks.crawler_item_loader()
        item_loader = ItemLoader(response=response, bookmark=bookmark)

        yield item_loader.load_item()
