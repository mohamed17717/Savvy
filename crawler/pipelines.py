class SQLitePipeline:
    def __init__(self) -> None:
        # because its block scrapy shell
        from crawler.orm import DjangoProxy
        self.dj_proxy = DjangoProxy()

    async def process_item(self, item, spider):
        meta_tags = item.get('meta_tags', [])
        headers = item.get('headers', [])
        url = item['url'][0]
        page_title = item.get('page_title', ['Undefined'])[0]

        bookmark = item.get('bookmark', [None])[0]

        await self.dj_proxy.webpage_write(bookmark, url, page_title, meta_tags, headers)
        await self.dj_proxy.store_bookmark_weights(bookmark)

        return item
