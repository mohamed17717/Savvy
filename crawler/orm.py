from asgiref.sync import sync_to_async

from App import models


@sync_to_async
def django_wrapper(func, *args, **kwargs):
    return func(*args, **kwargs)


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
