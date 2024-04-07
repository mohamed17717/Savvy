from . import FlowController
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from App.models import Bookmark


class YoutubeBookmarkFlowController(FlowController):
    # 1- no crawling // no store image // no webpage // no scrapes
    # 2- weight only the existing title and url
    # 3- using url patterns inject words weights

    DOMAIN = 'youtube.com'

    def __init__(self, bookmarks: list['Bookmark']) -> None:
        self.bookmarks = bookmarks

    @classmethod
    def get_weighting_serializer(cls):
        from App.serializers import YoutubeBookmarkWeightingSerializer
        return YoutubeBookmarkWeightingSerializer

    def run_flow(self) -> None:
        from App import tasks

        for bookmark in self.bookmarks:
            tasks.store_weights_task.delay(bookmark.id)
