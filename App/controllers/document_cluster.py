from typing import Generator

import numpy as np

from App.choices import CusterAlgorithmChoices as algo
from App.types import ClustersHolderType, ClusterType

from common.utils.function_utils import single_to_plural
from common.utils.matrix_utils import flat_matrix, filter_row_length_in_matrix


class ClusterMaker:
    '''Algorithm for Clustering Documents
    There is 2 algorithms i used for clustering
    1. transitive similarity (x == y and y == z, then x == z)
    2. Moving threshold similarity
    3. add non-clustered documents to the nearest document 
        cluster if similarity exceeded min threshold
    '''

    def __init__(self, documents: list[str], similarity_mx: np.ndarray):
        # immutable -> doc to sorted similarities
        # {doc_id: [(doc_id, similarity), ...]}
        similarity_mx_injected_by_documents = [
            sorted(zip(documents, i), key=lambda x: x[1], reverse=True)
            for i in similarity_mx
        ]
        self.similarity_dict = dict(
            zip(documents, similarity_mx_injected_by_documents))

        self.documents = documents.copy()
        self.similarity_mx = np.copy(similarity_mx)

        # threshold setup
        self.threshold_step = 5
        self.min_threshold = 30
        self.max_threshold = 95
        self.min_threshold_for_nearest_cluster = 15

        # it generate min overlap to 30% which is accepted
        self.high_correlated_overlap = 0.65

        # self.cluster_good_length = max(math.ceil(len(documents)*0.015), 10)
        self.cluster_good_length = 8

        self.clusters = ClustersHolderType()

    ### THRESHOLD SETUP ###
    @property
    def threshold_range(self) -> Generator[float, None, None]:
        _from = self.max_threshold
        _to = self.min_threshold-self.threshold_step
        _step = -self.threshold_step

        for i in range(_from, _to, _step):
            yield i/100

    def similarity_matrix_to_dict(self, threshold) -> dict[str, list]:
        results = {
            doc_id: [
                (other_id, similarity)
                for other_id, similarity in zip(self.documents, similarities)
                if similarity >= threshold and other_id != doc_id
            ]

            for doc_id, similarities in zip(self.documents, self.similarity_mx)
        }
        return results

    @property
    def similars_generator(self) -> Generator[list[ClusterType], None, None]:
        for threshold in self.threshold_range:
            similarity_dict = self.similarity_matrix_to_dict(threshold)
            if threshold >= self.high_correlated_overlap:
                similar = self.transitive_similarity(similarity_dict)
            else:
                similar = self.flat_similarity_algorithm(similarity_dict)

            yield similar

    ### Helper Functions ###
    def remove_doc(self, doc_id) -> None:
        try:
            index = self.documents.index(doc_id)
            self.documents.pop(index)
            self.similarity_mx = np.delete(self.similarity_mx, index, axis=0)
            self.similarity_mx = np.delete(self.similarity_mx, index, axis=1)
        except:
            pass

    ### ALGORITHMS ###
    def transitive_similarity(self, similarity_dict) -> list[ClusterType]:
        """it depned on similarity overlap between high correlated documents
        for example x is similar to y by 0.7 and y is similar to z by 0.7
        then x simialr to z by 0.4 or more
        which is accepted correlation
        """
        results = []
        while similarity_dict:
            doc_id = list(similarity_dict.keys())[0]
            similarities = similarity_dict.pop(doc_id)
            visited = [doc_id]

            cluster = ClusterType(self.clusters)
            cluster.append(doc_id, 1, algo.TRANSITIVE_SIMILARITY.value)

            while similarities:
                other_id, other_similarity = similarities.pop(0)
                if other_id in visited:
                    continue
                cluster.append(other_id, other_similarity, algo.TRANSITIVE_SIMILARITY.value)
                visited.append(other_id)
                similarities.extend(similarity_dict.pop(other_id, []))

            results.append(cluster)
        return results

    def flat_similarity_algorithm(self, similarity_dict) -> list[ClusterType]:
        results = []
        visited = []
        for doc_id, similarities in similarity_dict.items():
            if doc_id in visited:
                continue

            cluster = ClusterType(self.clusters)
            cluster.append(doc_id, 1, algo.EXCEL_THRESHOLD.value)

            if similarities:
                for other_id, other_similarity in similarities:
                    cluster.append(other_id, other_similarity, algo.EXCEL_THRESHOLD.value)

            visited.extend(cluster.value)
            results.append(cluster)
        return results

    def to_most_relative_cluster_algorithm(self, one_elm_clusters) -> None:
        """
        This algorithm aim to add the not clustered docs to nearest doc's cluster
        so the number of not clustered reduced as possible
        """
        for elm in one_elm_clusters:
            nearest_elm, correlation = self.similarity_dict[elm][1]
            if correlation*100 > self.min_threshold_for_nearest_cluster:
                # TODO get cluster with least correlation
                cluster = self.clusters.item_logger.get(nearest_elm)
                if cluster:
                    cluster[-1].append(elm, correlation, algo.NEAREST_DOC_CLUSTER.value)
                else:
                    # TODO skip nearest elm from the loop to not create 2 clusters with same data
                    cluster = ClusterType(self.clusters)
                    cluster.append(elm, correlation, algo.NEAREST_DOC_CLUSTER.value)
                    cluster.append(nearest_elm, correlation, algo.NEAREST_DOC_CLUSTER.value)
                    self.clusters.append(cluster)
            else:
                cluster = ClusterType(self.clusters)
                cluster.append(elm, 1, algo.NOTHING.value)
                self.clusters.append(cluster)

    ### CLUSTERING ###
    def make(self) -> list:
        remove_docs = single_to_plural(self.remove_doc)

        for similars in self.similars_generator:
            good_length_similars = filter(
                lambda x: len(x) >= self.cluster_good_length,
                similars
            )

            for sublist in good_length_similars:
                self.clusters.append(sublist)
                remove_docs(sublist)
        else:  # last loop
            one_length_similars = flat_matrix(
                filter_row_length_in_matrix(similars, eq=1)
            )
            bad_length_similars = filter(
                lambda x: self.cluster_good_length > len(x) > 1,
                similars
            )

            for sublist in bad_length_similars:
                self.clusters.append(sublist)
                remove_docs(sublist)

            self.to_most_relative_cluster_algorithm(one_length_similars)
            self.clusters.item_logger.merge_similar_clusters()

        return [
            cluster.store() for cluster in self.clusters
        ]
