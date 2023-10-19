from crawler.orm import DjangoProxy

dj_proxy = DjangoProxy()


class SQLitePipeline:
    async def process_item(self, item, spider):
        meta_tags = item.get('meta_tags', [])
        headers = item.get('headers', [])
        url = item['url'][0]
        page_title = item.get('page_title', ['Undefined'])[0]

        bookmark = item.get('bookmark', [None])[0]

        await dj_proxy.webpage_write(bookmark, url, page_title, meta_tags, headers)
        await dj_proxy.store_bookmark_weights(bookmark)

        return item
