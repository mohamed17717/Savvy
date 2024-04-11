from abc import ABC, abstractmethod
from common.utils.url_utils import is_valid_domain

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from App.models import Bookmark
    from rest_framework.serializers import Serializer
    from scrapy.loader import ItemLoader


class BookmarkHooks(ABC):
    _domain = None

    def __init__(self, bookmark: 'Bookmark') -> None:
        self.bookmark = bookmark
        super().__init__()

    @property
    @abstractmethod
    def domain(self) -> str:
        return self._domain

    @domain.setter
    def domain(self, value: str) -> None:
        if not is_valid_domain(value):
            raise ValueError('Invalid domain')
        self._domain = value

    def get_batch_method(self) -> callable:
        from App.tasks import crawl_bookmarks_task
        return crawl_bookmarks_task

    def post_batch(self) -> None:
        pass

    def get_weighting_serializer(self) -> 'Serializer':
        from App.serializers import BookmarkWeightingSerializer
        return BookmarkWeightingSerializer

    def crawler_cookies(self) -> dict:
        return {}

    def crawler_item_loader(self) -> 'ItemLoader':
        from crawler.items import BookmarkItemLoader
        return BookmarkItemLoader
