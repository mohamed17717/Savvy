from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rest_framework.serializers import Serializer
    from scrapy.loader import ItemLoader

    from App.models import Bookmark


class BookmarkHooks(ABC):
    def __init__(self, bookmark: "Bookmark") -> None:
        self.bookmark = bookmark
        super().__init__()

    @property
    def DOMAIN(self):
        raise NotImplementedError

    def get_batch_method(self) -> callable:
        from App.tasks import crawl_bookmarks_task

        return crawl_bookmarks_task

    def post_batch(self) -> None:
        pass

    def get_weighting_serializer(self) -> "Serializer":
        from App.serializers import BookmarkWeightingSerializer

        return BookmarkWeightingSerializer

    def crawler_cookies(self) -> dict:
        return {}

    def crawler_item_loader(self) -> "ItemLoader":
        from crawler.items import BookmarkItemLoader

        return BookmarkItemLoader
