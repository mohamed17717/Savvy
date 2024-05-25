import numpy as np
from App import models


class WordGraphBuilder:
    THRESHOLD = 20  # avoid float inaccuracy
    THRESHOLD_STEP = 4  # avoid float inaccuracy
    ACCEPTED_LEAF_LENGTH = 10
    MAXIMUM_THRESHOLD = 90

    def __init__(self, documents, similarity_matrix, threshold: int = THRESHOLD, parent=None, user=None):
        self.documents = documents
        self.similarity_matrix = similarity_matrix
        self.threshold = threshold
        self.parent = parent
        self.user = user or self.get_user()

    def get_user(self):
        from App.models import Bookmark
        bookmark = Bookmark.objects.filter(pk__in=self.documents).first()
        if bookmark is None:
            raise ValueError
        return bookmark.user

    def find_groups(self) -> list[list[int]]:
        n = len(self.similarity_matrix)  # Number of documents
        visited = [False] * n  # To track visited documents
        groups = []  # To store the final groups

        def dfs(doc_index, group):
            """ Depth-first search to find all connected documents """
            stack = [doc_index]
            while stack:
                current = stack.pop()
                if not visited[current]:
                    visited[current] = True
                    group.append(current)
                    # Consider all documents that are similar enough
                    for neighbor in range(n):
                        if self.similarity_matrix[current][neighbor] >= (self.threshold/100) and not visited[neighbor]:
                            stack.append(neighbor)

        for doc_index in range(n):
            if not visited[doc_index]:
                group = []
                dfs(doc_index, group)
                groups.append(group)

        return groups

    def group_to_documents(self, group: list[int]) -> list[str]:
        return [self.documents[index] for index in group]

    def group_to_sub_matrix(self, group: list[int]) -> list[list[float]]:
        return self.similarity_matrix[np.ix_(group, group)]

    def store_group(self, group: list[int], is_leaf=True, is_sharded_islands=False):
        node_kwargs = {
            'user': self.user,
            'parent': self.parent,
            'threshold': (self.threshold / 100),
            'bookmarks_count': len(group),
            'is_leaf': is_leaf,
            'is_sharded_islands': is_sharded_islands
        }

        if is_leaf:
            documents_ids = self.group_to_documents(group)
            bookmarks = models.Bookmark.objects.filter(pk__in=documents_ids)
            tags = models.Tag.objects.filter(
                bookmarks__in=bookmarks).distinct().order_by('-weight')[:10]

            m2m_data = {'tags': tags}
            node_kwargs['similarity_matrix'] = self.group_to_sub_matrix(
                group).tolist()
            m2m_data['bookmarks'] = bookmarks

            node = models.GraphNode(**node_kwargs)

            models.GraphNode.centralized_creator().add(node, m2m_data)
        else:
            node = models.GraphNode.objects.create(**node_kwargs)
        return node

    def graph_group(self, group, node):
        WordGraphBuilder(
            documents=self.group_to_documents(group),
            similarity_matrix=self.group_to_sub_matrix(group),
            threshold=self.threshold + self.THRESHOLD_STEP,
            parent=node,
            user=self.user
        ).build()

    def build(self):
        groups = self.find_groups()
        lengths = list(map(len, groups))
        is_sharded = [False] * len(groups)

        sharded_islands = []
        for index in range(len(groups)):
            if lengths[index] <= 3:
                sharded_islands.extend(groups[index])
                is_sharded[index] = True

        groups = [group for group, is_sharded in zip(groups, is_sharded) if not is_sharded]
        lengths = [length for length, is_sharded in zip(lengths, is_sharded) if not is_sharded]
        # groups.append(sharded_islands)

        first_level = self.parent is None
        last_level = self.threshold >= self.MAXIMUM_THRESHOLD

        # if groups are too small don't nest new level and increase threshold
        is_leaf_array = [
            last_level or length <= self.ACCEPTED_LEAF_LENGTH
            for length in lengths 
        ]
        nodes_count = is_leaf_array.count(False)
        if sharded_islands:
            self.store_group(sharded_islands, True, True)
            nodes_count += 1

        is_there_enough_nodes = first_level or last_level or nodes_count >= 2
        for is_leaf, group in zip(is_leaf_array, groups):
            if is_leaf or is_there_enough_nodes:
                node = self.store_group(group, is_leaf)
            else:
                # re-split on the same node
                node = self.parent

            if not is_leaf:
                self.graph_group(group, node)
