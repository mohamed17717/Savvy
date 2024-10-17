import cProfile
from time import time

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from App import controllers, models, types

bms = models.Bookmark.objects.all().order_by("?")


def c(func):
    p = cProfile.Profile()
    p.enable()
    func()
    p.print_stats("cumtime")
    p.disable()


def method1(bms):
    models.GraphNode.objects.all().delete()
    # all bookmarks by builder
    # bms = old + new
    # document_ids, vectors = models.WordWeight.word_vectors(bms)
    # similarity = types.SimilarityMatrixType(vectors, document_ids)
    #
    start = time()
    # similarity_matrix = similarity.similarity_matrix
    print(f"similarity_matrix time: {time() - start}")
    #
    start = time()
    # data = controllers.WordGraphBuilder(
    #     similarity.document_ids, similarity.similarity_matrix
    # ).build()
    print(f"graph time: {time() - start}")


def method2(new, old):
    models.GraphNode.objects.all().delete()
    #
    old_document_ids, old_vectors = models.WordWeight.word_vectors(old)
    similarity = types.SimilarityMatrixType(old_vectors, old_document_ids)
    # data = controllers.WordGraphBuilder(
    #     similarity.document_ids, similarity.similarity_matrix
    # ).build()
    #
    document_ids, vectors = models.WordWeight.word_vectors(new)
    similarity = types.SimilarityMatrixType(vectors, document_ids)
    #
    start = time()
    similarity_matrix = similarity.similarity_matrix
    print(f"similarity_matrix time: {time() - start}")

    #
    def unique_words(vectors):
        words = set()
        for v in vectors:
            words.update(v.keys())
        return words

    #
    def weight_matrix(vectors, unique_words=None):
        unique_words = unique_words
        return tuple(v.weight_vector(unique_words) for v in vectors)

    #
    unique_words = tuple(unique_words(vectors).union(unique_words(old_vectors)))
    w1 = weight_matrix(vectors, unique_words)
    w2 = weight_matrix(old_vectors, unique_words)
    #
    start = time()
    intersect_similarity = cosine_similarity(w1, w2)
    print(f"intersect_similarity time: {time() - start}")
    #
    print("start sleep")
    # sleep(15)
    models.GraphNode.centralized_creator().flush()
    print("end sleep")
    x = controllers.GraphNewNodes(
        document_ids, similarity_matrix, old_document_ids, intersect_similarity
    )
    start = time()
    x.run()
    print(f"update time: {time() - start=}")


def accuracy(bms, how_many):
    new = bms[:how_many]
    old = bms[how_many:]
    #
    method1(bms)
    print("start sleep")
    # sleep(15)
    models.GraphNode.centralized_creator().flush()
    print("end sleep")
    nodes_ids = {n: n.nodes.first().id for n in new}
    for n in new:
        n.nodes.clear()
    #
    method2(new, old)
    models.GraphNode.centralized_creator().flush()
    succeed = 0
    total = len(new)
    no_node = 0
    for n in new:
        mynode = n.nodes.first()
        if mynode is None:
            no_node += 1
        elif mynode.id == nodes_ids[n]:
            succeed += 1
    return succeed, no_node, total


def builder_time():
    models.GraphNode.objects.all().delete()
    bms = models.Bookmark.objects.all().order_by("?")
    document_ids, vectors = models.WordWeight.word_vectors(bms)
    similarity = types.SimilarityMatrixType(vectors, document_ids)
    start = time()
    similarity_matrix = similarity.similarity_matrix
    print(f"similarity_matrix time: {time() - start}")
    start = time()

    n = 5
    s = np.kron(similarity_matrix, np.ones((n, n)))
    d = similarity.document_ids * n

    start = time()
    # data = controllers.WordGraphBuilder(d, s).build()
    print(f"graph time: {time() - start}")
    print(s, d)


bms = models.Bookmark.objects.all().order_by("?")
# how_many = 662

# accuracy(bms, how_many)

# new = bms[:how_many]
# old = bms[how_many:]
# method1(bms)
# method2(new, old)


# print(models.GraphNode.centralized_creator().data)
