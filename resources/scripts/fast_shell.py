
from App import models, serializers
from pprint import pprint
from django.db.models import Count

bm = models.Bookmark.objects.get(pk=2399)
s = serializers.BookmarkWeightingSerializer(bm)
words = s.total_weight
ww = s.data

# stemming
pprint(list(bm.webpage.headers.all().values('level', 'text')))
pprint(list(bm.webpage.meta_tags.all().values('name', 'content')))

from App.controllers.text_cleaner import TextCleaner
x = ' '.join(bm.important_words)
print(x, TextCleaner(x).stemming(method='lem').text, sep='\n')

# update tags
models.Tag.objects.all().delete()
for bm in models.Bookmark.objects.all():
    bm.store_tags()


# get bm in clusters and has no webpage
clusters_ids = models.Bookmark.objects.filter(webpages__isnull=True, clusters__isnull=False).values_list('clusters', flat=True)
list(models.DocumentCluster.objects.filter(id__in=clusters_ids).annotate(bookmarks_count=Count('bookmarks')).values_list('bookmarks_count', flat=True))


# delete and cluster again
from App import models

models.DocumentCluster.objects.all().delete()
bookmarks = models.Bookmark.objects.all()
models.Bookmark.cluster_bookmarks(bookmarks)

# import cProfile
# p = cProfile.Profile()
# p.enable()
# p.print_stats('cumtime')
# p.disable()

# delete and refresh all words
models.DocumentWordWeight.objects.all().delete()
for bm in models.Bookmark.objects.all():
    bm.store_word_vector()
    
models.Bookmark.objects.filter(words_weights__isnull=True)
models.DocumentWordWeight.objects.filter(important=True)

# cosine similarity
from App import models, serializers
from App.controllers import document_cluster as doc_cluster


bookmarks = list(models.Bookmark.objects.all())

items_indexes = {b.id: i for i, b in enumerate(bookmarks)}
item_id = models.Bookmark.objects.get(title__icontains='Django Cook Book').id
item_index = items_indexes[item_id]

vectors = [b.important_words for b in bookmarks]

sim_calculator = doc_cluster.CosineSimilarityCalculator(vectors)
similarity_matrix = sim_calculator.similarity()


from pprint import pprint
from App import models
from App.controllers import document_cluster as doc_cluster

bookmarks = models.Bookmark.objects.all()
ids = [b.id for b in bookmarks]
vectors = [b.important_words for b in bookmarks]

sim_calculator = doc_cluster.CosineSimilarityCalculator(vectors)
similarity_matrix = sim_calculator.similarity()

clusters_maker = doc_cluster.ClusterMaker(ids, similarity_matrix)
clusters = clusters_maker.make()
pprint(clusters)


