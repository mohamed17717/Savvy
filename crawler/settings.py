BOT_NAME = "crawler"

SPIDER_MODULES = ["crawler.spiders"]
NEWSPIDER_MODULE = "crawler.spiders"

ROBOTSTXT_OBEY = False

DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
    'scrapy_fake_useragent.middleware.RandomUserAgentMiddleware': 400,
    'scrapy_fake_useragent.middleware.RetryUserAgentMiddleware': 401,

    'crawler.middlewares.LogResponseMiddleware': 543,  # Adjust the priority as needed
    # 'crawler.middlewares.ScrapeOpsRotateProxyMiddleware': 380,
}

ITEM_PIPELINES = {
    'crawler.pipelines.SQLitePipeline': 300,  # Adjust the priority as needed
}


REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"


# CUSTOM
FAKEUSERAGENT_PROVIDERS = [
    # This is the first provider we'll try
    'scrapy_fake_useragent.providers.FakeUserAgentProvider',
    # If FakeUserAgentProvider fails, we'll use faker to generate a user-agent string for us
    'scrapy_fake_useragent.providers.FakerProvider',
    # Fall back to USER_AGENT value
    'scrapy_fake_useragent.providers.FixedUserAgentProvider',
]

# Set Fallback User-Agent
USER_AGENT = 'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'

# DOWNLOAD_DELAY = 5
# RANDOMIZE_DOWNLOAD_DELAY = False
DOWNLOAD_TIMEOUT = 3
RETRY_TIMES = 3

# FEED_FORMAT = 'json'
# FEED_URI = 'crawler/output.json'
# DATABASE_PATH = 'crawler/sqlite.db'
STORAGE_PATH = 'crawler/response_bodies'

LOG_ENABLED = True  # Enable logging
LOG_FILE = 'logs/scrapy.log'
LOG_LEVEL = 'INFO'
