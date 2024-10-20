import typing
from abc import ABC

if typing.TYPE_CHECKING:
    from scrapy.loader import ItemLoader

    from App.models import Bookmark


class BookmarkHooks(ABC):
    def __init__(self, bookmark: "Bookmark") -> None:
        self.bookmark = bookmark
        super().__init__()

    @property
    def DOMAIN(self):
        raise NotImplementedError

    def get_batch_method(self) -> typing.Callable:
        from App.tasks import crawl_bookmarks_task

        return crawl_bookmarks_task

    def post_batch(self) -> None:
        pass

    def crawler_cookies(self) -> dict:
        return {}

    def crawler_item_loader(self) -> "ItemLoader":
        from crawler.items import BookmarkItemLoader

        return BookmarkItemLoader
