import typing

from .default import BookmarkHooks


class YoutubeBookmarkHooks(BookmarkHooks):
    # 1- no crawling // no store image // no webpage // no scrapes
    # 2- weight only the existing title and url
    # 3- using url patterns inject words weights

    DOMAIN = "youtube.com"

    def get_weighting_serializer(self):
        from App.serializers import YoutubeBookmarkWeightingSerializer

        return YoutubeBookmarkWeightingSerializer

    def get_batch_method(self) -> typing.Callable:
        from App.tasks import bulk_store_weights_task

        return bulk_store_weights_task
