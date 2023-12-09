from time import time
import scrapy
from urllib.parse import urlencode


class LogResponseMiddleware:
    def __init__(self) -> None:
        from crawler.orm import DjangoProxy
        self.dj_proxy = DjangoProxy()

    async def process_request(self, request, spider):
        exists = await self.dj_proxy.response_log_url_exists(request.url)
        if exists:
            # If the URL exists in the database, skip the request
            message = f"URL {request.url} already exists in the database. Skipping."
            spider.logger.info(message)
            raise scrapy.exceptions.IgnoreRequest()

    async def process_response(self, request, response, spider):
        # Store the URL, status code, and response body in a file, and store the file path in the database
        error_msg = None
        if response.status != 200:
            error_msg = f"HTTP status code {response.status}"

        await self.dj_proxy.response_log_write(request, response, spider, error_msg)

        # in case of failed crawled item
        start = time()
        bookmark = request.meta.get('bookmark')
        await self.dj_proxy.store_bookmark_weights(bookmark)
        print('Writing Failed weights: ', bookmark.url, ' in ', time() - start)

        return response

    async def process_exception(self, request, exception, spider):
        if isinstance(exception, scrapy.exceptions.IgnoreRequest):
            return None  # Do nothing for IgnoreRequest

        await self.dj_proxy.response_log_write(request, None, spider, str(exception))


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
