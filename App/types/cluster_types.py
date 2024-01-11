
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
        self.value = [] # clusters list
        self.correlation = {} # track correlation {cluster_index: correlation}
        self.items_map = {} # track item where {item: cluster_index}
        self.index = 0 # track length
        self.clustered_why = {} # track algorithm {item: algorithm}

    @property
    def repeated_items(self) -> dict:
        # return items that mentioned in many clusters
        return {
            k: v
            for k,v in self.items_map.items()
            if len(v) > 1
        }

    def merge_repeated_clusters(self):
        # [1] extract the couples
        # [2] know every couple repeated how many time
        couples = {}
        for repeating_list in self.repeated_items.values():
            _l = len(repeating_list)
            for i in range(_l-1):
                for j in range(i+1, _l):
                    name = f'{repeating_list[i]},{repeating_list[j]}'
                    couples.setdefault(name, 0)
                    couples[name] += 1
        # [3] know the length of the couple
        # [4] if the repeated excel 0.6 of the length of one of them -> then merge
        merged_map = {} # x to root
        for couple, times in couples.items():
            i1, i2 = tuple(map(int, couple.split(',')))
            l1, l2 = len(self.value[i1]) , len(self.value[i2])
            break_point = 0.7

            mini, maxi, l_mini, l_maxi = i1, i2, l1, l2
            if l1 > l2:
                mini, maxi, l_mini, l_maxi  = i2, i1, l2, l1

            if times/l_mini > break_point:
                root = maxi
                root_changed = False
                while merged_map.get(root) is not None:
                    root = merged_map[root]
                    root_changed = True
                # is mini consider root ? change it to the new maxi
                is_mini_consider_root_before = mini in merged_map.values()
                if is_mini_consider_root_before:
                    for k, v in merged_map.items():
                        if v == mini:
                            merged_map[k] = root

                # if root changed the new root should have relation to this mini
                # if not then can't merge this mini to this root
                has_relation = f'{mini},{root}' in couples.keys() or f'{root},{mini}' in couples.keys()
                if root_changed and not has_relation:
                    continue
                else:
                    merged_map[mini] = root

        merged_map_ordered_list = list(merged_map.items())
        merged_map_ordered_list.sort(key=lambda i: i[0], reverse=True)
        for point, root in merged_map_ordered_list:
            print(f'merged {point=} to {root=}, ({len(self.value)})')
            self.value[root].extend(self.value[point])
            self.value.pop(point)

    def append(self, cluster, *, correlation=0, algorithm=None) -> None:
        self.value.append(
            self.ListWrapper(cluster, self, self.index)
        )
        for item in cluster:
            self.items_map.setdefault(item, [])
            self.items_map[item].append(self.index)
            self.clustered_why[item] = algorithm # TODO key should contain item and cluster or add it inside the map

        self.correlation[self.index] = correlation
        self.index += 1

    def bulk_append(self, *clusters, correlation=0, algorithm=None):
        if clusters:
            for cluster in clusters:
                self.append(cluster, correlation=correlation, algorithm=algorithm)

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
            current_correlation = self.parent.correlation[self.index]

            def eqn(l1, c1, l2, c2):
                return (l1*c1 + l2*c2)/(l1+l2)

            return eqn(len(self), current_correlation, 1, new_correlation)

        def append(self, obj, *, correlation=0, algorithm=None):
            if self.parent:
                self.parent.items_map.setdefault(obj, [])
                self.parent.items_map[obj].append(self.index)
                self.parent.clustered_why[obj] = algorithm
                self.parent.correlation[self.index] = self.__avg_correlation(
                    correlation
                )

            return super().append(obj)
