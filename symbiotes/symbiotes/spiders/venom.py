import scrapy


class VenomSpider(scrapy.Spider):
    name = "venom"
    allowed_domains = ["venom.com"]
    start_urls = ["https://venom.com"]

    def parse(self, response):
        pass
