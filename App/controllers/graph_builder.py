import numpy as np

from App import models


class WordGraphBuilder:
    THRESHOLD = 0.20
    THRESHOLD_STEP = 0.04
    ACCEPTED_LEAF_LENGTH = 20

    def __init__(self, documents, similarity_matrix, threshold=THRESHOLD, parent=None, user=None):
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
                        if self.similarity_matrix[current][neighbor] >= self.threshold and not visited[neighbor]:
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

    def store_group(self, group: list[int], is_leaf=True):
        from App.models import Bookmark, Tag

        documents_ids = self.group_to_documents(group)
        node = models.WordGraphNode.objects.create(
            user=self.user,
            parent=self.parent,
            threshold=self.threshold,
            bookmarks_count=len(documents_ids)
        )

        bookmarks = Bookmark.objects.filter(pk__in=documents_ids)
        tags = Tag.objects.filter(bookmarks__in=bookmarks)
        tags = tags.order_by('-weight').distinct()[:10]

        node.tags.set(tags)
        if is_leaf:
            node.bookmarks.set(bookmarks)

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
        last_level = self.threshold >= 1

        for group in groups:
            is_leaf = last_level or len(group) <= self.ACCEPTED_LEAF_LENGTH 
            node = self.store_group(group, is_leaf)
            if not is_leaf:
                self.graph_group(group, node)
