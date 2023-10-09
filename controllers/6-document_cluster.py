from typing import Dict

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


class CosineSimilarityCluster:
    """Make blind similarity for the documents
    using algorithm for cosine similarity 
    """

    def __init__(self, documents: list[Dict[str, int]]) -> None:
        self.documents = documents

    @property
    def _unique_words(self) -> set:
        words = set()
        for doc in self.documents:
            words.update(doc.keys())
        return words

    @property
    def _weights_matrix(self):
        unique_words = self._unique_words
        weights_matrix = np.zeros((len(self.documents), len(unique_words)))

        for i, doc in enumerate(self.documents):
            for j, word in enumerate(unique_words):
                # set the defined weight in each document
                weights_matrix[i, j] = doc.get(word, 0)

        return weights_matrix

    def calculate_similarity(self):
        similarities = cosine_similarity(self._weights_matrix)
        return similarities

    def _cluster_docs(self, break_point: float = 0.4) -> Dict[int, list[int]]:
        similarities = self.calculate_similarity()

        sims = {}
        for doc_index, doc_sims in enumerate(similarities):
            sims[doc_index] = []
            for sim_index, sim in enumerate(doc_sims):
                # The file itself
                if doc_index == sim_index:
                    continue

                if sim >= break_point:
                    sims[doc_index].append((sim, sim_index))

        return sims

    def _merge_clusters(self, clustered_docs) -> list[list[int]]:
        merged = set()

        # Make sure we have unique clusters
        for doc_index, similarities in clustered_docs.items():
            cluster = [doc_index, *[idx for sim, idx in similarities]]
            cluster = sorted(cluster)
            cluster = map(str, cluster)
            cluster = ','.join(cluster)

            merged.add(cluster)

        # unpack indexes
        merged = [
            list(map(int, cluster.split(','))) for cluster in merged
        ]

        return merged

    def display(self):
        similarities = self.calculate_similarity()
        similarities = similarities.round(2)

        names = [f'Doc_{i}' for i, _ in enumerate(self.documents)]
        df = pd.DataFrame(similarities, index=names, columns=names)

        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)

        print('Result\n', df)

    def get_clusters(self, break_point: float = 0.4):
        clusters = self._cluster_docs(break_point)
        clusters = self._merge_clusters(clusters)

        return clusters


"""
There is 2 main tasks in this step
1- text clustering
    - cluster with context ->
            should use AI for understanding the text

2- labels the cluster (2 types)
    - ai with predefined labels and use one-shot-model 
    - ai without predefined
    - manual labels
        * website name
        * and the most repeated word in the documents 
        * or whatever algorithm
"""
