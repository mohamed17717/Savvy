
import numpy as np

from django.db import models
from django.contrib.auth import get_user_model


class WordGraphNode(models.Model):
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name='nodes')
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, related_name='children')

    tags = models.ManyToManyField('App.Tag', related_name='nodes', blank=True)
    bookmarks = models.ManyToManyField(
        'App.Bookmark', related_name='nodes', blank=True)
    bookmarks_count = models.PositiveSmallIntegerField(default=0)

    path = models.CharField(max_length=1024, blank=True,
                            null=True, db_index=True)
    threshold = models.FloatField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs) -> None:
        if self.pk is None and self.parent:
            path_list = []
            if self.parent.path:
                path_list.append(self.parent.path)
            path_list.append(self.parent.pk)

            self.path = '.'.join(map(str, path_list))
        return super().save(*args, **kwargs)

    @property
    def leafs(self):
        cls = self._meta.model
        path = self.path
        if self.path is None:
            path = f'{self.pk}'
        return cls.objects.filter(path__startswith=path, bookmarks__isnull=False)

    def get_bookmarks(self):
        from App.models import Bookmark

        if self.bookmarks.exists():
            bookmarks = self.bookmarks.all()
        else:
            bookmarks = Bookmark.objects.filter(
                nodes__in=self.leafs).distinct()
        return bookmarks


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
        node = WordGraphNode.objects.create(
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
