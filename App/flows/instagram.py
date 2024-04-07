from . import FlowController
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from App.models import Bookmark


class InstagramBookmarkFlowController(FlowController):
    # 1- clustering don't depend on crawling // no webpage // no scrapes
    # 2- don't weight the existing title and url because they are useless
    # 3- using url patterns inject words weights
    # 4- crawl with custom spider to store just the image

    DOMAIN = 'instagram.com'

    def __init__(self, bookmarks: list['Bookmark']) -> None:
        self.bookmarks = bookmarks

    @classmethod
    def get_weighting_serializer(cls):
        from App.serializers import InstagramBookmarkWeightingSerializer
        return InstagramBookmarkWeightingSerializer

    def run_flow(self) -> None:
        from App import tasks

        for bookmark in self.bookmarks:
            tasks.store_weights_task.delay(bookmark.id)

        # run the instagram spider -> get meta tags -> get image -> download & store image
        tasks.batch_bookmarks_to_crawl_without_callback_task.delay(
            [bookmark.id for bookmark in self.bookmarks])
