
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


class BookmarkStatusChoices(models.IntegerChoices):
    PENDING = 1, _('waiting for any status change')
    DONE = 2, _('no need to show anymore')
    ACHIEVED = 3, _('hide for now')

    __empty__ = None
    __default__ = PENDING
