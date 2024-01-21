from collections import namedtuple

from common.utils.array_utils import window_list
from common.utils.math_utils import balanced_avg


class ClustersHolderType:
    """This class type is basic 2D list with custom features
    1- tracking each item in which cluster
    2- tracking why its in this cluster
    3- tracking the length of the clusters
    4- track the correlation in each cluster
    5- track repeating in clusters
    6- merge clusters if they are almost identical by 70%
    """

    def __init__(self) -> None:
        self.value = []  # clusters list
        self.correlation = {}  # track correlation {cluster_index: correlation}
        self.items_map = {}  # track item where {item: cluster_index}
        self.index = 0  # track length
        self.clustered_why = {}  # track algorithm {item: algorithm}

    @property
    def repeated_items(self) -> dict:
        # return items that mentioned in many clusters
        return {
            k: v for k, v in self.items_map.items() if len(v) > 1
        }

    def merge_repeated_clusters(self):
        cluster_couples = self.ClusterCouplesHolderType(self)

        cluster_merge_map = {}  # x to root
        similarity_acceptance = 0.7
        for couple, times in cluster_couples.items():
            # know the length of the couple
            _long, _short = cluster_couples.couple_details(couple)

            # if the repeated excel x% of the length of one of them -> then merge
            is_very_similar = times/_short.length > similarity_acceptance

            if not is_very_similar:
                continue

            # calculate the root
            root = cluster_couples.graph_root(cluster_merge_map, _long.index)
            root_changed = root != _long.index

            # if root changed the new root should have relation to this short_index
            if root_changed and not cluster_couples.check_couple_has_relation(_short.index, root):
                continue

            # roots can't be normal nodes so check and replace shorts to its root
            cluster_merge_map = {
                key: (root if val == _short.index else val)
                for key, val in cluster_merge_map.items()
            }
            cluster_merge_map.update({_short.index: root})

        for point, root in sorted(cluster_merge_map.items(), key=lambda i: -i[0]):
            root_cluster = self.value[root]
            point_cluster = self.value[point]
            self.correlation[root] = balanced_avg(len(
                root_cluster), self.correlation[root], len(point_cluster), self.correlation[point])
            self.value[root].extend(self.value.pop(point))

    def append(self, cluster, correlation=0, algorithm=None) -> None:
        self.value.append(
            self.ClusterType(cluster, self, self.index)
        )
        for item in cluster:
            self.items_map.setdefault(item, [])
            self.items_map[item].append(self.index)
            # TODO key should contain item and cluster or add it inside the map
            self.clustered_why[item] = algorithm

        self.correlation[self.index] = correlation
        self.index += 1

    def bulk_append(self, *clusters, correlation=0, algorithm=None):
        if clusters:
            for cluster in clusters:
                self.append(cluster, correlation, algorithm)

    def __getitem__(self, index):
        return self.value[index]

    def __len__(self):
        return self.index

    class ClusterType(list):
        """ChildList type its a simple list with custom features
        1- know its parent
        2- know its index in its parent
        3- transmit the append to its parent
        """

        def __init__(self, value, parent: 'ClustersHolderType' = None, index: int = None):
            super().__init__(value)
            self.parent = parent
            self.index = index

        def __avg_correlation(self, new_correlation):
            correlation = self.parent.correlation.get(self.index, 1)
            avg = balanced_avg(len(self), correlation, 1, new_correlation)
            return avg

        def append(self, obj, correlation=0, algorithm=None):
            if self.parent:
                self.parent.items_map.setdefault(obj, [])
                self.parent.items_map[obj].append(self.index)
                self.parent.clustered_why[obj] = algorithm
                self.parent.correlation[self.index] = self.__avg_correlation(
                    correlation
                )

            return super().append(obj)

    class ClusterCouplesHolderType(dict):
        """
        This class aim to handle repetition in clusters and
        check the similarity between them to decide if they should
        be merged or not
        """

        def __init__(self, clusters: 'ClustersHolderType') -> None:
            self.clusters = clusters
            self.__setup()

        def __setup(self):
            """
            # [1] extract the couples
            # [2] know every couple repeated how many time
            """
            for repeating_list in self.clusters.repeated_items.values():
                _l = window_list(repeating_list, 2, step=1)
                _l = map(self.__name_couple, _l)
                for couple in _l:
                    self.setdefault(couple, 0)
                    self[couple] += 1

        def __name_couple(self, couple):
            return ','.join(map(str, couple))

        def __unname_couple(self, name):
            return tuple(map(int, name.split(',')))

        def check_couple_has_relation(self, a, b):
            return any([
                self.__name_couple((a, b)) in self.keys(),
                self.__name_couple((b, a)) in self.keys()
            ])

        def couple_details(self, couple_name):
            index1, index2 = self.__unname_couple(couple_name)
            length1, length2 = len(self.clusters[index1]), len(
                self.clusters[index2])

            Item = namedtuple('Item', ['index', 'length'])

            result = [Item(index1, length1), Item(index2, length2)]
            result.sort(key=lambda i: -i.length)

            return result

        def graph_root(self, graph: dict, node):
            root = node
            while graph.get(root) is not None:
                root = graph[root]
            return root
