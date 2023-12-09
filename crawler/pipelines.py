from time import time


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

        # in case of succeeded crawled item
        start = time()
        await self.dj_proxy.webpage_write(bookmark, url, page_title, meta_tags, headers)
        print('Writing webpage: ', url, ' in ', time() - start)

        start = time()
        await self.dj_proxy.store_bookmark_weights(bookmark)
        print('Writing weights: ', url, ' in ', time() - start)

        return item
