# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter

import os
import sqlite3
import hashlib
import scrapy



class SymbiotesSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class SymbiotesDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)



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
        database_path = settings.get('DATABASE_PATH')  # Set this in your settings
        storage_path = settings.get('STORAGE_PATH')  # Set this in your settings

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
        self.cursor.execute("SELECT COUNT(*) FROM url_status WHERE url = ?", (url,))
        count = self.cursor.fetchone()[0]

        # If count is greater than 0, the URL exists in the database
        return count > 0

    def process_request(self, request, spider):
        # Check if the URL exists in the database
        url_exists_in_database = self.check_url_in_database(request.url)

        if url_exists_in_database:
            # If the URL exists in the database, skip the request
            spider.logger.info(f"URL {request.url} already exists in the database. Skipping.")
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
