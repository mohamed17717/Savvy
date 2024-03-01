from App import tasks
from common.utils.async_utils import django_wrapper


class SQLitePipeline:
    async def process_item(self, item, spider):
        meta_tags = item.get('meta_tags', [])
        headers = item.get('headers', [])
        # url = item['url'][0]
        page_title = item.get('page_title', ['Undefined'])[0]

        bookmark = item.get('bookmark', [None])[0]

        if bookmark:
            # in case of succeeded crawled item
            await django_wrapper(tasks.store_webpage_task.apply_async, kwargs={
                'bookmark_id': bookmark.id,
                'page_title': page_title,
                'meta_tags': meta_tags,
                'headers': headers
            })
            await django_wrapper(tasks.store_weights_task.apply_async, kwargs={
                'bookmark_id': bookmark.id
            })

        return item
