
from App import models
import difflib



cluster0 = 'threshold-0.95-0ml9'
cluster1 = 'threshold-0.95-w4a0'


zero = models.Cluster.objects.get(name=cluster0)
one = models.Cluster.objects.get(name=cluster1)

zero_docs = sorted(list(zero.bookmarks.all().values_list('id', flat=True)))
one_docs = sorted(list(one.bookmarks.all().values_list('id', flat=True)))


sm=difflib.SequenceMatcher(None,zero_docs, one_docs)
sm.ratio()
sum([i.size for i in sm.get_matching_blocks()]) / len()

# -------------------------------------

from App import models
from django.db.models import Count
set(models.Bookmark.objects.all().annotate(c=Count('clusters')).values_list('c', flat=True).order_by('-c'))

models.Bookmark.objects.all().annotate(c=Count('clusters')).order_by('-c')[80]


# 10 GitHub Repositories every Developer should know - DEV Community
# QuerySet API reference | Django documentation | Django

