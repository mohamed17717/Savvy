from .default import BookmarkHooks


class FacebookBookmarkHooks(BookmarkHooks):
    # 1- no crawling // no store image // no webpage // no scrapes

    # TODO crawl using random cookies to make sure
    # we don't get banned and get valid results
    DOMAIN = "facebook.com"
