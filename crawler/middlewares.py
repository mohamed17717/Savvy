import scrapy
from scrapy.spidermiddlewares.offsite import OffsiteMiddleware

import os
import sqlite3
import hashlib

from urllib.parse import urlencode


class LogResponseMiddleware:
    def __init__(self, database_path, storage_path):
        self.database_path = database_path
        self.storage_path = storage_path
        self.conn = sqlite3.connect(database_path)
        self.cursor = self.conn.cursor()
        self.init_database()

    @classmethod
    def from_crawler(cls, crawler):
        # Retrieve settings from Scrapy settings.py
        settings = crawler.settings
        # Set this in your settings
        database_path = settings.get('DATABASE_PATH')
        # Set this in your settings
        storage_path = settings.get('STORAGE_PATH')

        # Initialize the middleware instance with the database and storage paths
        return cls(database_path, storage_path)

    def init_database(self):
        # Create a table to store URL status and file paths
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS url_status (
            id INTEGER PRIMARY KEY,
            url TEXT,
            status_code INTEGER,
            exception_message TEXT,
            response_file_path TEXT
        )''')
        self.conn.commit()

    def check_url_in_database(self, url):
        # Check if the URL exists in the 'url_status' table
        self.cursor.execute(
            "SELECT COUNT(*) FROM url_status WHERE url = ? AND exception_message IS NULL", (url,))
        count = self.cursor.fetchone()[0]

        # If count is greater than 0, the URL exists in the database
        return count > 0

    def process_request(self, request, spider):
        # Check if the URL exists in the database
        url_exists_in_database = self.check_url_in_database(request.url)

        if url_exists_in_database:
            # If the URL exists in the database, skip the request
            spider.logger.info(
                f"URL {request.url} already exists in the database. Skipping.")
            raise scrapy.exceptions.IgnoreRequest()

    def process_response(self, request, response, spider):
        # Store the URL, status code, and response body in a file, and store the file path in the database
        url = request.url
        status_code = response.status
        exception_message = None
        response_file_path = None

        if status_code != 200:
            exception_message = f"HTTP status code {status_code}"

        if response.body:
            # Create a unique file name based on the URL hash
            url_hash = hashlib.md5(url.encode()).hexdigest()
            file_name = f"{url_hash}.html"
            file_path = os.path.join(self.storage_path, file_name)

            # Save the response body to the file
            with open(file_path, 'wb') as f:
                f.write(response.body)

            response_file_path = file_path

        # Store the data in the database
        self.cursor.execute(
            "INSERT INTO url_status (url, status_code, exception_message, response_file_path) VALUES (?, ?, ?, ?)",
            (url, status_code, exception_message, response_file_path)
        )
        self.conn.commit()

        return response

    def process_exception(self, request, exception, spider):
        if isinstance(exception, scrapy.exceptions.IgnoreRequest):
            return None  # Do nothing for IgnoreRequest

        # Handle exceptions and store them in the database
        url = request.url
        exception_message = str(exception)
        response_file_path = None
        self.cursor.execute(
            "INSERT INTO url_status (url, exception_message, response_file_path) VALUES (?, ?, ?)",
            (url, exception_message, response_file_path)
        )
        self.conn.commit()

    def close_spider(self, spider):
        # Close the database connection when the spider is closed
        self.conn.close()


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
