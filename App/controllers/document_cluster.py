from typing import Dict, Generator

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
    '''Algorithm for Clustering Documents
    There is 2 algorithms i used for clustering
    1. transitive similarity (x == y and y == z, then x == z)
    2. Moving threshold similarity 
    '''

    def __init__(self, documents: list[str], similarity_mx: np.ndarray,):
        self.documents = documents
        self.similarity_mx = similarity_mx
        # threshold setup
        self.threshold_step = 4
        self.min_threshold = 30
        self.max_threshold = 65
        self.threshold = 65

        self.cluster_good_length = 8

    @property
    def threshold_range(self) -> Generator[float, None, None]:
        for i in range(self.max_threshold, self.min_threshold-self.threshold_step, -self.threshold_step):
            yield i/100

    def similarity_dict(self, threshold) -> dict[str, list]:
        results = {}
        for doc_id, similarities in zip(self.documents, self.similarity_mx):
            results[doc_id] = []
            for other_id, similarity in zip(self.documents, similarities):
                if doc_id == other_id:
                    continue  # skip self
                if similarity >= threshold:
                    results[doc_id].append(other_id)

        return results

    def transitive_similarity(self, similarity_dict) -> list[list]:
        results = []
        while similarity_dict:
            doc_id = list(similarity_dict.keys())[0]
            similarities = similarity_dict.pop(doc_id)
            visited = [doc_id]

            cluster = {doc_id}

            while similarities:
                other_id = similarities.pop(0)
                if other_id in visited:
                    continue
                cluster.add(other_id)
                visited.append(other_id)
                similarities.extend(similarity_dict.pop(other_id, []))

            results.append(cluster)
        return results

    def remove_doc(self, doc_id) -> None:
        index = self.documents.index(doc_id)
        self.documents.pop(index)
        self.similarity_mx = np.delete(self.similarity_mx, index, axis=0)
        self.similarity_mx = np.delete(self.similarity_mx, index, axis=1)

    def make(self) -> list[list]:
        clusters = []
        for threshold in self.threshold_range:
            similarity_dict = self.similarity_dict(threshold)
            similar = self.transitive_similarity(similarity_dict)

            last_loop = threshold*100 <= self.min_threshold
            if last_loop:
                similar = similar
            else:
                similar = [
                    x for x in similar
                    if len(x) > self.cluster_good_length]

            if similar:
                clusters.extend(similar)

                for sublist in similar:
                    for item in sublist:
                        self.remove_doc(item)

        return clusters
