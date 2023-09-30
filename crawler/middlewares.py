import scrapy
from urllib.parse import urlencode
from datetime import date, timedelta
from asgiref.sync import sync_to_async

from App import models


class LogResponseMiddleware:
    @sync_to_async
    def is_url_exists(self, url):
        print('\n\nURL EXIST CHECK\n\n')
        # if passed 50 days then scrape it again
        white_date = date.today() - timedelta(days=50)
        return models.ScrapyResponseLog.objects.filter(
            url=url, error__isnull=True, created_at__date__gte=white_date
        ).exists() and False

    def process_request(self, request, spider):
        pass
        # if self.is_url_exists(request.url):
        #     # If the URL exists in the database, skip the request
        #     message = f"URL {request.url} already exists in the database. Skipping."
        #     spider.logger.info(message)
        #     raise scrapy.exceptions.IgnoreRequest()

    @sync_to_async
    def write_to_django(self, request, response, spider, error_msg=None):
        log = models.ScrapyResponseLog.objects.create(
            bookmark=spider.bookmark,
            url=request.url,
            status_code=response.status if response else 500,
            error=error_msg,
        )
        if response:
            log.store_file(response.body)

    async def process_response(self, request, response, spider):
        print('\n\nWRITING\n\n')
        # Store the URL, status code, and response body in a file, and store the file path in the database
        error_msg = None
        if response.status != 200:
            error_msg = f"HTTP status code {response.status}"

        await self.write_to_django(request, response, spider, error_msg)

        return response

    async def process_exception(self, request, exception, spider):
        if isinstance(exception, scrapy.exceptions.IgnoreRequest):
            return None  # Do nothing for IgnoreRequest

        await self.write_to_django(request, None, spider, str(exception))


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
