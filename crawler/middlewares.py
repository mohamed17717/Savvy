from urllib.parse import urlencode

from App import tasks, models
from common.utils.async_utils import django_wrapper


class LogResponseMiddleware:
    async def process_response(self, request, response, spider):
        # Store the URL, status code, and response body in a file, and store the file path in the database
        error_msg = None
        if response.status != 200:
            error_msg = f"HTTP status code {response.status}"

        bookmark = request.meta.get('bookmark')
        
        bookmark.process_status = models.Bookmark.ProcessStatus.CRAWLED.value
        await bookmark.asave(update_fields=['process_status'])

        log = await models.ScrapyResponseLog.objects.acreate(
            bookmark=bookmark, status_code=response.status, error=error_msg
        )
        await django_wrapper(log.store_file, response.body)
        # in case of failed crawled item
        await django_wrapper(tasks.store_weights_task.apply_async, kwargs={'bookmark_id': bookmark.id})
        return response

    async def process_exception(self, request, exception, spider):
        bookmark = request.meta.get('bookmark')
        
        bookmark.process_status = models.Bookmark.ProcessStatus.CRAWLED_ERROR.value
        await bookmark.asave(update_fields=['process_status'])
        await models.ScrapyResponseLog.objects.acreate(
            bookmark=bookmark, status_code=500, error=str(exception)
        )


class ScrapeOpsRotateProxyMiddleware:
    DOMAIN = 'proxy.scrapeops.io'

    def get_proxy_url(self, url):
        API_KEY = 'b89ad8f8-a2f2-4e89-a8eb-844dbb0ead32'
        payload = {'api_key': API_KEY, 'url': url}
        proxy_url = f'https://{self.DOMAIN}/v1/?{urlencode(payload)}'

        return proxy_url

    def process_request(self, request, spider):
        if self.DOMAIN not in request.url:
            proxy_url = self.get_proxy_url(request.url)
            request = request.replace(url=proxy_url)

            return request

    def spider_opened(self, spider):
        if self.DOMAIN not in spider.allowed_domains:
            spider.allowed_domains.append(self.DOMAIN)

        spider.logger.info('Spider opened: %s' % spider.name)
