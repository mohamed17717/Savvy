from django.db import transaction
from App import models

from asgiref.sync import sync_to_async


class SQLitePipeline:
    @sync_to_async
    def do_django(self, spider, url, page_title, meta_tags, headers):
        with transaction.atomic():
            webpage = models.BookmarkWebpage.objects.create(
                bookmark=spider.bookmark,
                url=url, title=page_title)

            # models.WebpageMetaTag.bulk_create(webpage, meta_tags)
            tag_objects = []
            for tag in meta_tags:
                tag_objects.append(models.WebpageMetaTag(
                    webpage=webpage, name=tag.get('name', 'UNKNOWN'),
                    content=tag.get('content'), attrs=tag
                ))
            models.WebpageMetaTag.objects.bulk_create(tag_objects)

            # models.WebpageHeader.bulk_create(webpage, headers)
            header_objects = []
            for hhh in headers:
                for header, texts in hhh.items():
                    level = int(header.strip('h'))  # [1-6]
                    for text in texts:
                        header_objects.append(
                            models.WebpageHeader(
                                webpage=webpage, text=text, level=level)
                        )
            models.WebpageHeader.objects.bulk_create(header_objects)

    async def process_item(self, item, spider):
        print('\n\nITEM:', item, '\n\n')
        meta_tags = item.get('meta_tags', [])
        headers = item.get('headers', [])
        url = item['url'][0]
        page_title = item.get('page_title', ['Undefined'])[0]

        await self.do_django(spider, url, page_title, meta_tags, headers)

        return item
