from django.db import transaction

from asgiref.sync import sync_to_async

from App import models


class DjangoProxy:
    @sync_to_async
    def response_log_url_exists(self, url):
        return models.ScrapyResponseLog.is_url_exists(url)

    @sync_to_async
    def response_log_write(self, request, response, spider, error_message=None):
        log = models.ScrapyResponseLog.objects.create(
            bookmark=spider.bookmark,
            url=request.url,
            status_code=response.status if response else 500,
            error=error_message,
        )
        if response:
            log.store_file(response.body)

    @sync_to_async
    def webpage_write_meta_tags(self, webpage, tags):
        return models.WebpageMetaTag.bulk_create(webpage, tags)

    @sync_to_async
    def webpage_write_headers(self, webpage, headers):
        return models.WebpageHeader.bulk_create(webpage, headers)

    @sync_to_async
    def webpage_write(self, spider, url, page_title, meta_tags, headers):
        with transaction.atomic():
            webpage = models.BookmarkWebpage.objects.create(
                bookmark=spider.bookmark,
                url=url, title=page_title
            )

            self.webpage_write_meta_tags(webpage, meta_tags)
            self.webpage_write_headers(webpage, headers)

    @sync_to_async
    def store_bookmark_weights(self, bookmark):
        bookmark.store_word_vector()
