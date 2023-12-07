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
            bookmark=request.meta.get('bookmark'),
            url=request.url,
            status_code=response.status if response else 500,
            error=error_message,
        )
        if response:
            log.store_file(response.body)

    @sync_to_async
    def webpage_write(self, bookmark, url, page_title, meta_tags, headers):
        with transaction.atomic():
            webpage = models.BookmarkWebpage.objects.create(
                bookmark=bookmark, url=url, title=page_title
            )

            models.WebpageMetaTag.bulk_create(webpage, meta_tags)
            models.WebpageHeader.bulk_create(webpage, headers)

    @sync_to_async
    def store_bookmark_weights(self, bookmark):
        bookmark.store_word_vector()
        bookmark.store_tags()

    @sync_to_async
    def cluster_bookmarks(self, bookmarks):
        return models.Bookmark.cluster_bookmarks(bookmarks)
