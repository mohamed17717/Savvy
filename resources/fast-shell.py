
from App import models
from django.db.models import Count
from pprint import pprint

def cluster_duplicates_bookmarks():
    return models.Bookmark.objects.annotate(
        clusters_count=Count('clusters')).filter(clusters_count__gt=1)

def not_clustered_bookmarks():
    return models.Bookmark.objects.filter(clusters__isnull=True)

def one_bookmark_cluster():
    return models.Cluster.objects.filter(bookmarks_count=1)

def important_words_percent():
    return models.WordWeight.objects.filter(important=True).count() / models.WordWeight.objects.count() * 100

def cluster_related_to_tag(tag_name):
    return models.Cluster.objects.filter(bookmarks__tags__name=tag_name).distinct()

def cluster_by_name(name):
    return models.Cluster.objects.get(name=name)

def words_vectors_for_cluster(cluster_name):
    return [bm.important_words for bm in models.Cluster.objects.get(name=cluster_name).bookmarks.all()]

def how_it_look(cluster_name, index):
    cluster = cluster_by_name(cluster_name)
    bookmark = cluster.bookmarks.all()[index]
    html_file = bookmark.scrapes.last().html_file
    return 'http://localhost' + html_file.url, bookmark


bms = not_clustered_bookmarks()

# sorted(cluster_duplicates_bookmarks().values_list('clusters_count', flat=True))
# cluster_duplicates_bookmarks().count() # 168
# not_clustered_bookmarks().count() # 60
# one_bookmark_cluster().count() # 234
# important_words_percent() # 88%

# c_name = 'cluster power 0.567 contain 9 items'
# pprint(words_vectors_for_cluster(c_name))
# how_it_look(c_name, 1)
