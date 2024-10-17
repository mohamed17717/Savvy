from functools import cached_property

import numpy as np
from django.db.models import Sum

from App import models


class GraphThresholdConfig:
    START = 20
    MIDDLE = 50
    STOP = 90
    STEP = 10

    def _next(self, current=None):
        if current is None:
            return self.MIDDLE / 100

        current *= 100
        if current >= self.STOP:
            return
        elif current < self.MIDDLE:
            return
        return (current + self.STEP) / 100

    def _prev(self, current=None):
        if current is None:
            return self.MIDDLE / 100

        current *= 100
        if current <= self.START:
            return
        elif current > self.MIDDLE:
            return
        return (current - self.STEP) / 100


class GraphGroupType(list):
    MINIMUM_LENGTH = 4
    LEAF_LENGTH = 50

    def __init__(self, group: list, threshold, ids, similarity_mx):
        # self = group
        super().__init__(group)

        self.length = len(group)
        self.threshold = threshold
        self.ids = ids
        self.similarity_mx = similarity_mx

    @property
    def is_very_small(self):
        return self.length < self.MINIMUM_LENGTH

    @property
    def is_leaf(self):
        return self.length <= self.LEAF_LENGTH

    @cached_property
    def __high_words(self):
        return (
            models.WordWeight.objects.filter(bookmark_id__in=self.ids)
            .values("word")
            .annotate(total_weight=Sum("weight"))
            .order_by("-total_weight")[:10]
            .values_list("word", flat=True)
        )

    @property
    def __m2m_fields(self):
        bookmarks = models.Bookmark.objects.filter(pk__in=self.ids)
        tags = models.Tag.objects.filter(name__in=self.__high_words)
        return {"bookmarks": bookmarks, "tags": tags}

    def __get_node_instance(self, user, parent):
        instance = models.GraphNode(
            user=user,
            parent=parent,
            threshold=self.threshold,
            bookmarks_count=self.length,
            is_leaf=self.is_leaf,
            name=", ".join(self.__high_words),
        )

        return instance

    def store_leaf(self, user, parent, is_island=False):
        instance = self.__get_node_instance(user, parent)

        if is_island:
            instance.is_leaf = True
            instance.is_sharded_islands = True

        instance.similarity_matrix = self.similarity_mx.tolist()

        models.GraphNode.centralized_creator().add(instance, self.__m2m_fields)

        return instance

    def store_node(self, user, parent):
        instance = self.__get_node_instance(user, parent)
        instance.save()
        return instance


class GraphGroupsFinder:
    def __init__(self, ids, similarity_mx, threshold):
        self.ids = ids
        self.similarity_mx = similarity_mx
        self.threshold = threshold

    def to_type(self, group):
        ids = self.group_to_ids(group)
        similarity_mx = self.group_to_similarity_mx(group)
        return GraphGroupType(group, self.threshold, ids, similarity_mx)

    def find(self) -> list[GraphGroupType]:
        n = len(self.similarity_mx)  # Number of documents
        visited = [False] * n  # To track visited documents
        groups = []  # To store the final groups

        def dfs(doc_index, group):
            """Depth-first search to find all connected documents"""
            stack = [doc_index]
            while stack:
                current = stack.pop()
                if not visited[current]:
                    visited[current] = True
                    group.append(current)
                    # Consider all documents that are similar enough
                    for neighbor in range(n):
                        if (
                            self.similarity_mx[current][neighbor] >= (self.threshold)
                            and not visited[neighbor]
                        ):
                            stack.append(neighbor)

        for doc_index in range(n):
            if not visited[doc_index]:
                group = []
                dfs(doc_index, group)
                groups.append(group)

        return map(self.to_type, groups)

    def group_to_ids(self, group) -> list[str]:
        return [self.ids[index] for index in group]

    def group_to_similarity_mx(self, group: list[int]) -> list[list[float]]:
        return self.similarity_mx[np.ix_(group, group)]

    def find_classified(self):
        groups = self.find()
        islands, leafs, nodes = [], [], []

        for group in groups:
            if group.is_very_small:
                islands.extend(group)
            elif group.is_leaf:
                leafs.append(group)
            else:
                nodes.append(group)

        return islands, leafs, nodes


class GraphBuilder:
    def __init__(self, ids, similarity_mx):
        self.ids = ids
        self.similarity_mx = similarity_mx

        self.user = self.__get_user()
        self.threshold = GraphThresholdConfig()

    def __get_user(self):
        bookmark = models.Bookmark.objects.filter(pk__in=self.ids).first()
        if bookmark is None:
            raise ValueError
        return bookmark.user

    def build(self, root=None, ids=None, similarity_mx=None, threshold=None):
        if ids is None:
            ids = self.ids
        if similarity_mx is None:
            similarity_mx = self.similarity_mx
        if threshold is None:
            threshold = self.threshold._next()

        groups_finder = GraphGroupsFinder(ids, similarity_mx, threshold)
        islands, leafs, nodes = groups_finder.find_classified()

        if islands:
            islands_ids = groups_finder.group_to_ids(islands)
            islands_similarity_mx = groups_finder.group_to_similarity_mx(islands)
            prev_threshold = self.threshold._prev(threshold)
            islands = GraphGroupType(
                islands, threshold, islands_ids, islands_similarity_mx
            )
            # STORE if -> prev is None or islands.is_leaf
            if prev_threshold is None or islands.is_leaf:
                islands.store_leaf(self.user, root, is_island=True)
            else:
                self.build(None, islands_ids, islands_similarity_mx, prev_threshold)

        # check to re-split root on bigger threshold
        next_threshold = self.threshold._next(threshold)
        if len(leafs) + len(nodes) < 2 and root and next_threshold:
            self.build(root, ids, similarity_mx, next_threshold)
            return

        for leaf in leafs:
            leaf.store_leaf(self.user, root)

        for node in nodes:
            next_threshold = self.threshold._next(threshold)
            if next_threshold is None:
                node.store_leaf(self.user, root)
            else:
                node_instance = node.store_node(self.user, root)
                self.build(node_instance, node.ids, node.similarity_mx, next_threshold)
