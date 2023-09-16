import scrapy
from symbiotes.items import BookmarkItemLoader


class VenomSpider(scrapy.Spider):
    name = "venom"
    # allowed_domains = ["venom.com"]
    # start_urls = ["https://venom.com"]

    def start_requests(self):
        # TODO read urls dynamically
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
        bookmark_item_loader = BookmarkItemLoader(response=response)

        bookmark_item_loader.add_value('meta_tags', [
            meta.attrib
            for meta in response.xpath('//head/meta')
        ])
        bookmark_item_loader.add_value('page_title', response.xpath(
            '//head/title/text()').extract_first())
        bookmark_item_loader.add_value('url', response.url)
        bookmark_item_loader.add_value('headers', {
            f'h{i}': response.xpath(f'//h{i}//text()').extract()
            for i in range(1, 6+1)
        })

        # Yield the loaded Item
        yield bookmark_item_loader.load_item()
