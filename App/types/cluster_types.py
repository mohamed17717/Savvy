
class ClustersHolderType:
    """This class type is basic 2D list with custom features
    1- tracking each item in which cluster
    2- tracking why its in this cluster
    3- tracking the length of the clusters
    4- track the correlation in each cluster
    """

    def __init__(self) -> None:
        self.value = []
        self.correlation = {}
        self.items_map = {}
        self.index = 0
        self.clustered_why = {}

    def append(self, cluster, *, correlation=None, algorithm=None) -> None:
        self.value.append(
            self.ListWrapper(cluster, self, self.index)
        )
        for item in cluster:
            self.items_map[item] = self.index
            self.clustered_why[item] = algorithm

        if correlation is not None:
            self.correlation[self.index] = correlation

        self.index += 1

    def __getitem__(self, index):
        return self.value[index]

    def __len__(self):
        return self.index

    class ListWrapper(list):
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
            self.parent.correlation.setdefault(self.index, 1)

            current_correlation = self.parent.correlation.get[self.index]

            def eqn(l1, c1, l2, c2):
                return (l1*c1 + l2*c2)/(l1+l2)

            return eqn(len(self), current_correlation, 1, new_correlation)

        def append(self, obj, *, correlation=None, algorithm=None):
            if self.parent:
                self.parent.items_map[obj] = self.index
                self.parent.clustered_why[obj] = algorithm

                if correlation is not None:
                    self.parent.correlation[self.index] = self.__avg_correlation(
                        correlation
                    )

            return super().append(obj)
