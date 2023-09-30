from django.db import transaction
from App import models


class SQLitePipeline:
    def process_item(self, item, spider):
        meta_tags = item.get('meta_tags', [])
        headers = item.get('headers', [])
        url = item['url'][0]
        page_title = item['page_title'][0]

        with transaction.atomic():
            webpage = models.BookmarkWebpage.objects.create(
                url=url, title=page_title)
            models.WebpageMetaTag.bulk_create(webpage, meta_tags)
            models.WebpageHeader.bulk_create(webpage, headers)

        return item
