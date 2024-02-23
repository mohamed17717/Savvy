from asgiref.sync import sync_to_async

from App import models


@sync_to_async
def django_wrapper(func, *args, **kwargs):
    return func(*args, **kwargs)


class DjangoProxy:
    @sync_to_async
    def bookmark_parent(self, bookmarks):
        return bookmarks[0].parent_file

    @sync_to_async
    def response_log_write(self, request, response, spider, error_message=None):
        log = models.ScrapyResponseLog.objects.create(
            bookmark=request.meta.get('bookmark'),
            status_code=response.status if response else 500,
            error=error_message,
        )
        if response:
            log.store_file(response.body)
