
import os
import glob
import shutil


from App import models, types
from django.db.models import Count
from django.db import models as dj_models
from App.controllers.graph_builder import WordGraphBuilder
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


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


def delete_everything():
    for model_name in dir(models):
        model = getattr(models, model_name)
        try:
            if issubclass(model, dj_models.Model) and 'App' in model.__module__:
                print('Start deleting', model)
                model.objects.all().delete()
        except Exception:
            pass

def system_zero():
    for f in glob.glob("./logs/*.log"):
        print('[remove] ', f)
        os.remove(f)
    for d in glob.glob('./media/*'):
        print('[remove] ', d)
        shutil.rmtree(d)
    print('delete database')
    delete_everything()


def export_services_logs():
    # not work from shell
    services = [
        'django', 
        'celery_orm_worker', 
        'celery_scrapy_worker',
        'celery_download_images_worker',
    ]
    for s in services:
        os.system(f'docker-compose logs {s} > {s}.log')


def build_graph():
    models.GraphNode.objects.all().delete()

    bookmarks = models.Bookmark.objects.all()
    document_ids, vectors = models.WordWeight.word_vectors(bookmarks)
    similarity = types.SimilarityMatrixType(vectors, document_ids)

    maker = WordGraphBuilder(similarity.document_ids,
                             similarity.similarity_matrix)
    maker.build()
    models.GraphNode.centralized_creator().flush()


def analyze_graph():
    bookmark_nodes_count = set(models.Bookmark.objects.annotate(
        nodes_count=Count('nodes')).values_list('nodes_count', flat=True))
    nodes_count = models.GraphNode.objects.all().count()
    roots_count = models.GraphNode.objects.filter(
        parent__isnull=True).count()
    leafs_count = models.GraphNode.objects.filter(
        bookmarks__isnull=False).distinct().count()
    thresholds = sorted(
        set(models.GraphNode.objects.values_list('threshold', flat=True)))
    # paths = list(models.GraphNode.objects.values_list('path', flat=True))
    bookmarks_on_leafs = list(models.GraphNode.objects.filter(
        bookmarks__isnull=False).distinct().values_list('bookmarks_count', flat=True))
    # children_count = sorted(models.GraphNode.objects.annotate(
    #     children_count=Count('children')).values_list('children_count', flat=True))

    print(f'{bookmark_nodes_count=}')
    print(f'{nodes_count=}')
    print(f'{roots_count=}')
    print(f'{leafs_count=}')
    print(f'{thresholds=}')
    # print(f'{paths=}')
    print(f'{bookmarks_on_leafs=}')
    # print(f'{children_count=}')


def similarity_between_nodes():
    parent = models.GraphNode.objects.all()[0]
    children = parent.leafs
    node1, node2 = children[0], children[1]

    node1_docs, node1_vectors = models.WordWeight.word_vectors(
        node1.bookmarks.all())
    node2_docs, node2_vectors = models.WordWeight.word_vectors(
        node2.bookmarks.all())

    def unique_words(vectors):
        words = set()
        for v in vectors:
            words.update(v.keys())
        return words

    def weight_matrix(vectors, unique_words):
        vector = [0] * len(unique_words)
        weights = {}
        for v in vectors:
            for word in unique_words:
                weights.setdefault(word, 0)
                weights[word] += v.get(word, 0)
        for i, word in enumerate(unique_words):
            vector[i] = weights[word]
        return [vector]

    # def weight_matrix(vectors, unique_words):
    #     return np.array([[v.get(word, 0) for word in unique_words] for v in vectors])

    # Combine dimensions
    unique_words = tuple(unique_words(
        node1_vectors).union(unique_words(node2_vectors)))
    intersect_similarity = cosine_similarity(
        weight_matrix(node1_vectors, unique_words),
        weight_matrix(node2_vectors, unique_words)
    )
    print(np.average(intersect_similarity))

# bms = not_clustered_bookmarks()

# sorted(cluster_duplicates_bookmarks().values_list('clusters_count', flat=True))
# cluster_duplicates_bookmarks().count() # 168
# not_clustered_bookmarks().count() # 60
# one_bookmark_cluster().count() # 234
# important_words_percent() # 88%

# c_name = 'cluster power 0.567 contain 9 items'
# pprint(words_vectors_for_cluster(c_name))
# how_it_look(c_name, 1)
