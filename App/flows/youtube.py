import typing

from .default import BookmarkHooks


class YoutubeBookmarkHooks(BookmarkHooks):
    # 1- no crawling // no store image // no webpage // no scrapes
    # 3- using url patterns inject words weights

    DOMAIN = "youtube.com"

    # TODO go to next step not crawl nor store weights
    def get_batch_method(self) -> typing.Callable:
        pass
