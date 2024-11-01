import typing

from common.utils.array_utils import window_list

from .default import BookmarkHooks


class InstagramBookmarkHooks(BookmarkHooks):
    # 1- clustering don't depend on crawling // no webpage // no scrapes
    # 4- crawl with custom spider to store just the image

    DOMAIN = "instagram.com"

    def get_batch_method(self) -> typing.Callable:
        pass

    def post_batch(self) -> typing.Callable:
        def method(bookmark_ids):
            from App import tasks

            batch_size = 30
            id_groups = window_list(bookmark_ids, batch_size)

            for group in id_groups:
                tasks.crawl_bookmarks_task.delay(group)

        return method
