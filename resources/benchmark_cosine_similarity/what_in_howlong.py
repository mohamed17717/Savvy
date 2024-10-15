import random
from time import time

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def run1(docs_count, words_count):
    matrix = np.zeros((docs_count, words_count))
    for i in range(docs_count):
        for j in range(words_count):
            matrix[i, j] = round(random.random(), 3)
    start = time()
    cosine_similarity(matrix)
    return time() - start


def run2(docs_count, words_count, new_docs_count):
    matrix = np.zeros((docs_count, words_count))
    for i in range(docs_count):
        for j in range(words_count):
            matrix[i, j] = round(random.random(), 3)
    start = time()
    sim_matrix = cosine_similarity(matrix)
    old_time = time() - start
    new_start = time()
    for i in range(new_docs_count):
        doc_vector = np.zeros(words_count)
        for j in range(words_count):
            doc_vector[j] = round(random.random(), 3)
        sim_vector = [cosine_similarity([doc_vector, row])[0, 1] for row in matrix]
        matrix = np.vstack((matrix, doc_vector))
        sim_matrix = np.vstack((sim_matrix, np.array(sim_vector)))
        sim_matrix = np.hstack(
            (sim_matrix, np.atleast_2d(np.array(sim_vector + [1])).T)
        )
    new_time = time() - new_start
    total_time = time() - start
    print(f"{sim_matrix.shape=}")
    return f"{old_time=}, {new_time=}, {total_time=}"


def run3(docs_count, words_count, new_docs_count):
    matrix = np.zeros((docs_count, words_count))
    for i in range(docs_count):
        for j in range(words_count):
            matrix[i, j] = round(random.random(), 3)

    sim_matrix = cosine_similarity(matrix)

    new_matrix = np.zeros((new_docs_count, words_count))
    for i in range(new_docs_count):
        for j in range(words_count):
            new_matrix[i, j] = round(random.random(), 3)

    start = time()
    new_sim_matrix = cosine_similarity(new_matrix)
    rel_sim_matrix = cosine_similarity(new_matrix, matrix)
    print(time() - start)

    sim_matrix = np.vstack((sim_matrix, rel_sim_matrix))
    rel_sim_matrix = np.rot90(rel_sim_matrix, k=1)[::-1]
    rel_sim_matrix = np.vstack((rel_sim_matrix, new_sim_matrix))
    sim_matrix = np.hstack((sim_matrix, rel_sim_matrix))

    total_matrix = np.vstack((matrix, new_matrix))
    # print(total_matrix)
    # print('---------------------------')
    # print(cosine_similarity(total_matrix))
    # print('---------------------------')
    # print(sim_matrix)
    # print('---------------------------')
    return sim_matrix == cosine_similarity(total_matrix)


run3(docs_count=3000, words_count=7000, new_docs_count=400)

"""
>>> run(docs_count=500, words_count=1000)
0.008362770080566406
>>> run(docs_count=500, words_count=1000)
0.008056879043579102
>>> run(docs_count=500, words_count=1000)
0.013321161270141602
>>> run(docs_count=500, words_count=3000)
0.02667403221130371
>>> run(docs_count=500, words_count=3000)
0.07260775566101074
>>> run(docs_count=1000, words_count=3000)
0.08974361419677734
>>> run(docs_count=1000, words_count=3000)
0.08242607116699219
>>> run(docs_count=1500, words_count=5000)
0.5461149215698242
>>> run(docs_count=1500, words_count=7000)
0.39356088638305664
>>> run(docs_count=1500, words_count=7000)
0.5706820487976074
>>> run(docs_count=5000, words_count=7000)
3.9821410179138184
>>> run(docs_count=10000, words_count=7000)
12.566219329833984
>>> run(docs_count=10000, words_count=10000)
18.452751398086548
>>> run(docs_count=15000, words_count=15000)
64.37098670005798
>>> run(docs_count=15000, words_count=10000)
40.906790018081665
>>> run(docs_count=20000, words_count=10000)
109.52635502815247
>>> run(docs_count=15000, words_count=7000)
41.6205940246582
>>> run(docs_count=20000, words_count=7000)
75.3759822845459
"""
