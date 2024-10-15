import scrapy
from scrapy.loader import ItemLoader


class BookmarkItem(scrapy.Item):
    meta_tags = scrapy.Field()
    headers = scrapy.Field()
    page_title = scrapy.Field()
    bookmark = scrapy.Field()


class BookmarkItemLoader(ItemLoader):
    default_item_class = BookmarkItem  # Specify the Item class

    def strip_whitespace_from_dict(self, values):
        def clean_headers(headers: dict):
            # structure is {h1: [text1, text2], h2: [text1, text2]}
            cleaned_headers = {}
            for tag_name, texts in headers.items():
                texts = [text.strip() for text in texts]
                texts = filter(lambda i: i, texts)
                texts = list(texts)
                if texts:
                    cleaned_headers[tag_name] = texts
            return cleaned_headers

        values = map(clean_headers, values)
        values = filter(lambda i: i, values)
        values = list(values)

        return values

    headers_out = strip_whitespace_from_dict

    def __init__(self, item=None, selector=None, response=None, parent=None, **context):
        self.response = response
        self.bookmark = context.pop("bookmark", None)
        super().__init__(item, selector, response, parent, **context)

    def __get_headers(self, response):
        def extract_headers(hx):
            return {hx: response.xpath(f"//{hx}//text()").extract()}

        headers = map(lambda i: f"h{i}", range(1, 6 + 1))
        headers = map(extract_headers, headers)
        headers_dict = {}
        for h in headers:
            headers_dict.update(h)
        return headers_dict

    def load_item(self):
        # remove all style tags because if there is
        # a style tag inside body, will decrease accuracy
        self.response.xpath("//style").drop()
        self.response.xpath("//script").drop()

        meta_tags = [meta.attrib for meta in self.response.xpath("//head/meta")]
        page_title = self.response.xpath("//head/title/text()").extract_first()

        self.add_value("meta_tags", meta_tags)
        self.add_value("page_title", page_title)
        self.add_value("headers", self.__get_headers(self.response))
        self.add_value("bookmark", self.bookmark)

        return super().load_item()
