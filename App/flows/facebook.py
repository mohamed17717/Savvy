from .default import BookmarkHooks


class FacebookBookmarkHooks(BookmarkHooks):
    # 1- no crawling // no store image // no webpage // no scrapes
    # 2- weight only the existing title and url
    # 3- using url patterns inject words weights

    # TODO crawl using random cookies to make sure
    # we don't get banned and get valid results
    DOMAIN = "facebook.com"

    def get_weighting_serializer(self):
        from App.serializers import FacebookBookmarkWeightingSerializer

        return FacebookBookmarkWeightingSerializer

    def get_batch_method(self) -> callable:
        from App.tasks import bulk_store_weights_task

        return bulk_store_weights_task
