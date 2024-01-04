
from django.db import models
from django.utils.translation import gettext_lazy as _


class CusterAlgorithmChoices(models.IntegerChoices):
    TRANSITIVE_SIMILARITY = 1, _(
        'Transitive Similarity: if (x == y and y == z) then (x == z)')
    EXCEL_THRESHOLD = 2, _(
        'Excel Threshold: Similarity excel the threshold number')
    NEAREST_DOC_CLUSTER = 3, _(
        'Nearest Document\'s Cluster: add non-clustered documents to nearest document cluster if similarity exceeded min threshold')

    __empty__ = None
    __default__ = TRANSITIVE_SIMILARITY
