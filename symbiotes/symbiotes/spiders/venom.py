import scrapy
import json


class VenomSpider(scrapy.Spider):
    name = "venom"
    # allowed_domains = ["venom.com"]
    # start_urls = ["https://venom.com"]

    def start_requests(self):
        urls = [
            "https://www.kali.org/",
            "https://www.kali.org/tools/",
            "https://www.kali.org/docs/",
            "https://forums.kali.org/",
            "https://www.kali.org/kali-nethunter/",
            "https://www.exploit-db.com/",
            "https://www.exploit-db.com/google-hacking-database",
            "https://www.offensive-security.com/",
            "https://www.xnxx.com/search/lesbian",
            "https://www.xnxx.com/search/%D8%B3%D9%83%D8%B3?top",
            "https://www.xnxx.com/search/%D8%B3%D9%83%D8%B3+%D9%85%D8%B5%D8%B1%D9%8A+%D8%AC%D8%AF%D9%8A%D8%AF?top",
            "https://www.xnxx.com/search/big_tits",
            "https://www.xnxx.com/search/xnxx?top",
            "https://demo.florinz.com/",
            "https://demo.florinz.com/login",
            "https://www.pornhub.com/view_video.php?viewkey=ph5e7df37a9faf5",
            "https://www.pornhub.com/view_video.php?viewkey=ph625c9129718eb",
            "https://www.pornhub.com/view_video.php?viewkey=645552a40ff00",
            "https://ziziniashop.com/product-category/%d8%a7%d8%ac%d9%87%d8%b2%d9%87-%d8%a7%d9%84%d9%85%d8%b3%d8%a7%d8%ac/",
        ]

        for url in urls:
            domain = url.split('://')[1].split('/')[0]
            self.allowed_domains = [domain]
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        # TODO Extract all possible data that may help
        #   - meta
        #   - headers
        #   - page title
        #   - url
        # TODO add proxy middleware
        # TODO save every link with its response info (code, error message, ...)
        # TODO save every item in db
        # TODO read links dynamically

        meta_tags = response.xpath('//head/meta').extract()
        # self.log(f'{response.request.headers}')
        # self.log(f'[{response.status}] {response.url}')
        # self.log(meta_tags)
        # self.log('\n\n')
