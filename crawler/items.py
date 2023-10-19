import scrapy
from scrapy.loader import ItemLoader


class BookmarkItem(scrapy.Item):
    meta_tags = scrapy.Field()
    headers = scrapy.Field()
    url = scrapy.Field()
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
