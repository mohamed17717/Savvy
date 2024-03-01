import uuid
import numpy as np

from common.utils.array_utils import window_list
from common.utils.math_utils import balanced_avg


class ClusterType:
    """This class represent the cluster and its operations
    it will track
    -> correlation
    -> items
    -> why item in cluster
    -> length
    -> merge to another if similarity passed 70%

    also it track
    -> parent
    """

    def __init__(self, parent=None):
        self.id = uuid.uuid4().int & (1 << 64) - 1
        self.parent = parent
        self.value = []
        self.correlation = 1
        self.length = 0
        self.why = []

        # clusters merges
        self.merge_parent = None

    @property
    def name(self):
        return f'cluster power {self.correlation} contain {self.length} items'

    def append(self, item, correlation=0, algorithm=None):
        self.value.append(item)
        self.why.append(algorithm)
        self.length += 1
        self.correlation = balanced_avg(
            self.length, self.correlation, 1, correlation)

        return self

    def store(self):
        from App.models import Cluster, Bookmark

        RCs = Bookmark.objects.filter(id__in=self.value)
        user = RCs[0].user

        cluster = Cluster.objects.create(
            user=user, name=self.name, correlation=self.correlation)
        cluster.bookmarks.set(RCs)

        return cluster

    def merge_with(self, child):
        if self.merge_parent:
            self.merge_parent.merge_with(child)
        else:
            self.value.extend(child.value)
            self.correlation = balanced_avg(
                self.length, self.correlation,
                child.length, child.correlation
            )
            self.length += child.length
            self.why.extend(child.why)

            child.merge_parent = self
            self.parent.value = list(
                filter(lambda item: item is not child, self.parent.value))

    def __len__(self):
        return self.length

    def __iter__(self):
        return iter(self.value)

    def __str__(self) -> str:
        return f'cluster {self.length} items'

    def __repr__(self) -> str:
        return f'<cluster {self.length} items/>'

    def __eq__(self, other):
        return self.id == other.id


class ClusterItemLoggerType(dict):
    """Map that log each item in which cluster/s"""

    def __init__(self):
        super().__init__()

        self.cluster_id = {}  # str: ClusterType

    def log(self, item, cluster):
        self.setdefault(item, [])
        self[item].append(cluster)
        self.cluster_id[cluster.id] = cluster

    @property
    def _clusters_shared_items_counter_matrix(self):
        """Tell how many item is shared between cluster x and cluster y"""
        clusters_2d = {k: v for k, v in self.items() if len(v) > 1}.values()

        length = len(self.cluster_id)
        counter_matrix = np.zeros((length, length))
        id_to_index = dict(zip(self.cluster_id.keys(), range(length)))
        index_to_id = dict(zip(id_to_index.values(), id_to_index.keys()))

        for clusters in clusters_2d:
            for couple in window_list(clusters, 2, step=1):
                c1, c2 = couple
                index1, index2 = id_to_index[c1.id], id_to_index[c2.id]

                counter_matrix[index1, index2] += 1
                counter_matrix[index2, index1] += 1

        return counter_matrix, index_to_id

    def merge_similar_clusters(self):
        length = len(self.cluster_id)
        counter_matrix, index_to_id = self._clusters_shared_items_counter_matrix

        similarity_acceptance = 0.7
        for i in range(length):
            for j in range(i, length):
                id1, id2 = index_to_id[i], index_to_id[j]
                c1, c2 = self.cluster_id[id1], self.cluster_id[id2]
                _long, _short = c1, c2
                if c1.length < c2.length:
                    _long, _short = c2, c1

                times = counter_matrix[i, j]
                is_very_similar = times/_short.length > similarity_acceptance

                already_merged = _short.merge_parent is not None
                if not is_very_similar or already_merged:
                    continue

                _long.merge_with(_short)
        return True


class ClustersHolderType:
    """This class type is basic 2D list with custom features
    - log each item in which cluster/s
    - store all clusters in a list
    - ability to merge clusters if they are almost identical
    """

    def __init__(self) -> None:
        self.value = []  # clusters list
        self.item_logger = ClusterItemLoggerType()

    def append(self, cluster: ClusterType) -> None:
        if type(cluster) is not ClusterType:
            raise ValueError('It only accept `ClusterType` objects')

        for item in cluster:
            self.item_logger.log(item, cluster)

        self.value.append(cluster)

    def __getitem__(self, index):
        return self.value[index]

    def __len__(self):
        return len(self.value)

    def __iter__(self):
        return iter(self.value)
