from typing import Dict

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class CosineSimilarityCalculator:
    def __init__(self, documents: list[Dict[str, int]]) -> None:
        """Calculate similarity blindly between documents based on cosine similarity algorithm

        Args:
            documents (list[Dict[str, int]]): a list of word weight vector for each document, eg: [{word: weight, word2: weight}]
        """
        self.documents = documents

    @property
    def _unique_words(self) -> set:
        words = set()
        for doc in self.documents:
            words.update(doc.keys())
        return words

    @property
    def _doc_to_word_weight_matrix(self):
        weight_matrix = np.zeros(
            (len(self.documents), len(self._unique_words))
        )

        for i, doc in enumerate(self.documents):
            for j, word in enumerate(self._unique_words):
                # set the defined weight in each document
                weight_matrix[i, j] = doc.get(word, 0)

        return weight_matrix

    def similarity(self) -> np.ndarray:
        return cosine_similarity(self._doc_to_word_weight_matrix)


class ClusterMaker:
    def __init__(self, documents: list[str], similarity_mx: np.ndarray, break_point: float):
        """generate the clusters for the docs based on similarity matrix and breakpoint

        Args:
            documents (list[str]): list of documents ids
            similarity_mx (np.ndarray): matrix of len(documents) tell similarity between them
            break_point (float): point where we consider docs are similar or not
        """
        self.documents = documents
        self.similarity_mx = similarity_mx
        self.break_point = break_point
        self._clusters = None

    # getters
    def __get_clusters(self):
        return self._clusters or self.clusters()

    # methods
    def clusters(self) -> dict[str, list]:
        """cluster docs

        Returns:
            dict[str, list]: dict contain doc_id to its others similar to
                            others get as (doc_id, similarity)
                            eg: { doc1: [doc2, doc3] }
        """
        results = {}
        for doc_id, similarities in zip(self.documents, self.similarity_mx):
            results[doc_id] = []
            for other_id, similarity in zip(self.documents, similarities):
                if doc_id == other_id:
                    continue  # skip self

                if similarity >= self.break_point:
                    #  { doc1: [(doc2, 0.4), (doc3, 0.8)] }
                    # results[doc_id].append((other_id, similarity))
                    results[doc_id].append(other_id)

        self._clusters = results
        return results

    def clusters_flat(self) -> list[list]:
        # Merge Clusters Algorithm
        clusters = self.__get_clusters()
        # { doc1: [doc2, doc3] }

        results = []
        visited = []
        while clusters:
            doc_id = list(clusters.keys())[0]
            similarities = clusters.pop(doc_id)

            cluster = {doc_id}

            # if x == y and y == z, then x == z
            while similarities:
                other_id = similarities.pop(0)
                if other_id in visited:
                    continue
                cluster.add(other_id)
                visited.append(other_id)
                similarities.extend(clusters.pop(other_id, []))

            results.append(cluster)
        return results
