import typing

from .default import BookmarkHooks


class YoutubeBookmarkHooks(BookmarkHooks):
    # 1- no crawling // no store image // no webpage // no scrapes

    DOMAIN = "youtube.com"

    def get_batch_method(self) -> typing.Callable:
        pass
