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

        # TODO if needed convert it to signals and values
        self.tell_parent(item)

        return self

    def tell_parent(self, item):
        if self.parent:
            self.parent.items_map.setdefault(item, [])
            self.parent.items_map[item].append(self)

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
                self.length, self.correlation, child.length, child.correlation)
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
        self.items_map = {}  # track item where {item: cluster_index}

    @property
    def repeated_items(self) -> dict:
        # return items that mentioned in many clusters
        return {
            k: v for k, v in self.items_map.items() if len(v) > 1
        }

    def merge_repeated_clusters(self):
        cluster_couples = self.ClusterCouplesHolderType(self)

        similarity_acceptance = 0.7
        for couple, times in cluster_couples.items():
            # know the length of the couple
            _long, _short = cluster_couples.couple_details(couple)

            # if the repeated excel x% of the length of one of them -> then merge
            is_very_similar = times/_short.length > similarity_acceptance

            already_merged = _short.merge_parent is not None
            if not is_very_similar or already_merged:
                continue

            _long.merge_with(_short)

    def append(self, cluster_list, correlation=0, algorithm=None) -> None:
        if type(cluster_list) is ClusterType:
            cluster = cluster_list
        else:
            cluster = ClusterType(self)
            for item in cluster_list:
                cluster.append(item, correlation, algorithm)

        self.value.append(cluster)

    def __getitem__(self, index):
        return self.value[index]

    def __len__(self):
        return len(self.value)

    def __iter__(self):
        return iter(self.value)

    class ClusterCouplesHolderType(dict):
        """
        This class aim to handle repetition in clusters and
        check the similarity between them to decide if they should
        be merged or not
        """

        def __init__(self, clusters: 'ClustersHolderType') -> None:
            self.clusters = clusters
            self.id_map = {}  # contain id of couple and which couple are those
            self.__setup()

        def __setup(self):
            """
            # [1] extract the couples
            # [2] know every couple repeated how many time
            """
            for repeating_list in self.clusters.repeated_items.values():
                couples = list(window_list(repeating_list, 2, step=1))
                couples_names = (map(self.__name_couple, couples))
                for name, couple in zip(couples_names, couples):
                    self.setdefault(name, 0)
                    self[name] += 1
                    self.id_map[name] = couple

        def __name_couple(self, couple):
            name = map(id, couple)
            name = map(str, name)
            name = ','.join(name)
            return name

        def __unname_couple(self, name):
            return self.id_map[name]

        def couple_details(self, couple_name):
            cluster1, cluster2 = self.__unname_couple(couple_name)
            result = [cluster1, cluster2]
            result.sort(key=lambda i: -i.length)

            return result
