from App import tasks


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
        tasks.store_webpage_task.apply_async(kwargs={
            'bookmark': bookmark,
            'url': url,
            'page_title': page_title,
            'meta_tags': meta_tags,
            'headers': headers
        })
        tasks.store_weights_task.apply_async(kwargs={
            'bookmark': bookmark
        })

        return item
