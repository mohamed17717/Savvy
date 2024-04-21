
import numpy as np

from copy import deepcopy
from django.db import models
from django.contrib.auth import get_user_model


class WordGraphNode(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='nodes')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, related_name='children')    

    tags = models.ManyToManyField('App.Tag', related_name='nodes', blank=True)
    bookmarks = models.ManyToManyField('App.Bookmark', related_name='nodes', blank=True)
    bookmarks_count = models.PositiveSmallIntegerField(default=0)
    
    path = models.CharField(max_length=1024, blank=True, null=True, db_index=True)
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
            bookmarks = Bookmark.objects.filter(nodes__in=self.leafs).distinct()
        return bookmarks


class WordGraphMaker:
    THRESHOLD = 0.20
    THRESHOLD_STEP = 0.04
    MINIMUM_CHILDREN = 2
    ACCEPTED_LEAF_LENGTH = 20

    def __init__(self, documents, similarity_matrix):
        self.documents = documents
        self.similarity = self.convert_similarity_matrix(similarity_matrix) # {doc_id: [(doc_id, similarity), ...]}
        self.user = self.get_user()

    def get_user(self):
        from App.models import Bookmark
        bookmark = Bookmark.objects.filter(pk__in=self.documents).first()
        if bookmark is None:
            raise ValueError
        return bookmark.user

    def convert_similarity_matrix(self, similarity_matrix) -> dict[str, list]:
        similarity = {}
        docs = self.documents

        index = 0
        for doc, row in zip(docs, similarity_matrix):
            row = list(zip(docs[index+1:], row[index+1:]))
            similarity[doc] = row
            index += 1
        return similarity

    def filter_similarity_by_threshold(self, similarity, threshold) -> dict[str, list]:
        return {
            doc: [
                doc_id for doc_id, doc_similarity in row 
                if doc_similarity >= threshold 
                # and similarity.get(doc_id, None) is not None
            ]
            for doc, row in similarity.items()
        }

    def split_clusters(self, clusters) -> tuple[list[str], list[str]]:
        nodes = [
            cluster
            for cluster in clusters
            if len(cluster) <= self.ACCEPTED_LEAF_LENGTH
        ]
        clusters = [
            cluster
            for cluster in clusters
            if len(cluster) > self.ACCEPTED_LEAF_LENGTH
        ]
        return clusters, nodes

    def transitive_similarity(self, similarity: dict[str, list]) -> list[list[str]]:
        results = []
        visited = []

        while similarity:
            doc = list(similarity.keys())[0]
            similarities = set(similarity.pop(doc))
            cluster = [doc]
            
            if doc in visited:
                continue

            while similarities:
                other_doc = similarities.pop()

                if other_doc in visited: #or similarity.get(other_doc, None) is None:
                    continue

                cluster.append(other_doc)
                visited.append(other_doc)
                
                other_similarities = set(similarity.get(other_doc, []))
                other_similarities -= set(visited)
                similarities = similarities.union(other_similarities)

            results.append(cluster)
        return results

    def store_node(self, node_data, threshold, parent, is_leaf=True):
        from App.models import Bookmark, Tag

        node = WordGraphNode.objects.create(
            user=self.user,
            parent=parent,
            threshold=threshold,
            bookmarks_count=len(node_data)
        )

        bookmarks = Bookmark.objects.filter(pk__in=node_data)
        tags = Tag.objects.filter(bookmarks__in=bookmarks)
        node.tags.set(tags.order_by('-weight').distinct()[:10])

        if is_leaf:
            node.bookmarks.set(bookmarks)

        return node

    def build_graph(self, similarity, threshold, parent=None):
        filtered_similarity = self.filter_similarity_by_threshold(similarity, threshold)
        clusters = self.transitive_similarity(deepcopy(filtered_similarity))
        clusters, nodes = self.split_clusters(clusters)

        if threshold >= 1: # don't split cluster nodes anymore
            nodes.extend(clusters)
            clusters = []

        for node in nodes:            
            self.store_node(node, threshold, parent)
        
        if len(clusters) == 1:
            threshold += self.THRESHOLD_STEP
            self.build_graph(similarity, threshold, parent)
            return

        threshold += self.THRESHOLD_STEP
        for cluster in clusters:
            cluster_node = self.store_node(cluster, threshold, parent, is_leaf=False)
            cluster_similarity = {
                doc: self.similarity[doc]
                for doc in cluster
            }

            self.build_graph(cluster_similarity, threshold, cluster_node)


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

    def build(self):
        groups = self.find_groups()

        for group in groups:
            is_leaf = len(group) <= self.ACCEPTED_LEAF_LENGTH or self.threshold >= 1
            node = self.store_group(group, is_leaf)
            if not is_leaf:
                sub_matrix = self.group_to_sub_matrix(group)
                sub_docs = self.group_to_documents(group)
                more_threshold = self.threshold + self.THRESHOLD_STEP
                WordGraphBuilder(sub_docs, sub_matrix, more_threshold, node, self.user).build()


    # def build_with_less_depth(self):
    #     groups = self.find_groups()
        
    #     def is_leaf(group):
    #         return len(group) <= self.ACCEPTED_LEAF_LENGTH or self.threshold >= 1

    #     leafs_flags = list(map(is_leaf, groups))

    #     # Reduce tree depth
    #     if self.threshold < 1 and leafs_flags.count(False) >= self.MINIMUM_CHILDREN:
    #         more_threshold = self.threshold + self.THRESHOLD_STEP
    #         return WordGraphBuilder(
    #             self.documents, self.similarity_matrix, 
    #             more_threshold, self.parent, self.user
    #         ).build()

    #     for is_leaf, group in zip(leafs_flags, groups):
    #         node = self.store_group(group, is_leaf)
    #         if not is_leaf:
    #             sub_matrix = self.group_to_sub_matrix(group)
    #             sub_docs = self.group_to_documents(group)
    #             more_threshold = self.threshold + self.THRESHOLD_STEP
    #             WordGraphBuilder(sub_docs, sub_matrix, more_threshold, node, self.user).build()
