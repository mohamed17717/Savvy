
from django.db import models
from django.utils.translation import gettext_lazy as _


class CusterAlgorithmChoices(models.IntegerChoices):
    TRANSITIVE_SIMILARITY = 1, _(
        'Transitive Similarity: if (x == y and y == z) then (x == z)')
    EXCEL_THRESHOLD = 2, _(
        'Excel Threshold: Similarity excel the threshold number')
    NEAREST_DOC_CLUSTER = 3, _(
        'Nearest Document\'s Cluster: add non-clustered documents to nearest document cluster if similarity exceeded min threshold')
    NOTHING = 4, _(
        'Not clustered by any algorithm.'
    )

    __empty__ = None
    __default__ = TRANSITIVE_SIMILARITY


class BookmarkUserStatusChoices(models.IntegerChoices):
    PENDING = 1, _('waiting for any status change')
    DONE = 2, _('no need to show anymore')
    ACHIEVED = 3, _('hide for now')

    __empty__ = None
    __default__ = PENDING


class BookmarkProcessStatusChoices(models.IntegerChoices):
    CLONED = 10, _('cloned from another user bookmark (to status 60)')
    CREATED = 20, _('created')

    START_CRAWL = 30, _('sent to scrapy crawler')
    CRAWLED_ERROR = 35, _('crawled failed for any reason')
    CRAWLED = 40, _('crawled succeeded')

    START_TEXT_PROCESSING = 50, _('start text processing')
    TEXT_PROCESSED = 60, _('text processed')

    START_CLUSTER = 70, _('start clustering process')
    CLUSTERED = 80, _('done the whole flow')

    __empty__ = None
    __default__ = CREATED
