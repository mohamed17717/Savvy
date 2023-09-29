import scrapy
from urllib.parse import urlencode

from App import models


class LogResponseMiddleware:
    def process_request(self, request, spider):
        if models.ScrapyResponseLog.is_url_exists(request.url):
            # If the URL exists in the database, skip the request
            message = f"URL {request.url} already exists in the database. Skipping."
            spider.logger.info(message)
            raise scrapy.exceptions.IgnoreRequest()

    def process_response(self, request, response, spider):
        # Store the URL, status code, and response body in a file, and store the file path in the database
        url = request.url
        status_code = response.status
        exception_message = None

        if status_code != 200:
            exception_message = f"HTTP status code {status_code}"

        log = models.ScrapyResponseLog.objects.create(
            url=url,
            status_code=status_code,
            error=exception_message,
        )
        log.store_file(response.body)

        return response

    def process_exception(self, request, exception, spider):
        if isinstance(exception, scrapy.exceptions.IgnoreRequest):
            return None  # Do nothing for IgnoreRequest

        models.ScrapyResponseLog.objects.create(
            url=request.url,
            status_code=500,
            error=str(exception)
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
