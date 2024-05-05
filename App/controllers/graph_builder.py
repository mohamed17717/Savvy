import numpy as np

from django.db.models import Q

from App import models


class WordGraphBuilder:
    THRESHOLD = 20  # avoid float inaccuracy
    THRESHOLD_STEP = 4  # avoid float inaccuracy
    ACCEPTED_LEAF_LENGTH = 20
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

    def store_group(self, group: list[int], is_leaf=True):
        from App.models import Bookmark, Tag

        documents_ids = self.group_to_documents(group)
        node = models.GraphNode.objects.create(
            user=self.user,
            parent=self.parent,
            threshold=(self.threshold / 100),
            bookmarks_count=len(documents_ids),
            is_leaf=is_leaf
        )

        bookmarks = Bookmark.objects.filter(pk__in=documents_ids)
        tags = Tag.objects.filter(bookmarks__in=bookmarks)
        tags = tags.order_by('-weight').distinct()[:10]

        node.tags.set(tags)
        if is_leaf:
            node.bookmarks.set(bookmarks)
            node.similarity_matrix = self.group_to_sub_matrix(group).tolist()
            node.save(update_fields=['similarity_matrix'])

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
        first_level = self.parent is None
        last_level = self.threshold >= self.MAXIMUM_THRESHOLD

        # if clusters are too small don't nest new level and increase threshold
        is_leaf_array = [
            last_level or len(group) <= self.ACCEPTED_LEAF_LENGTH
            for group in groups
        ]
        nodes_count = is_leaf_array.count(False)
        is_there_enough_nodes = first_level or last_level or nodes_count >= 2

        for is_leaf, group in zip(is_leaf_array, groups):
            if is_leaf or is_there_enough_nodes:
                node = self.store_group(group, is_leaf)
            else:
                # re-split on the same node
                node = self.parent

            if not is_leaf:
                self.graph_group(group, node)


class GraphBuildingRouter:
    def __init__(self, documents, similarity_matrix, old_documents, intersected_similarity) -> None:
        self.documents = documents
        self.similarity_matrix = similarity_matrix
        self.old_documents = old_documents
        self.intersected_similarity = intersected_similarity

    def route(self):
        # if incoming data is large enough delete old and recreate all together
        large_factor = 1000/400 # 2.5 # if new is 400 and old is 1000 -> consider large enough to delete 1000
        is_large_enough = len(self.documents) * large_factor > len(self.old_documents)
        
        if is_large_enough:
            self.user.nodes.delete()


class GraphNewNodes:
    def __init__(self, documents, similarity_matrix, old_documents, intersected_similarity, user=None) -> None:
        self.documents = documents
        self.similarity_matrix = similarity_matrix
        self.old_documents = old_documents
        self.intersected_similarity = intersected_similarity
        
        self.user = user or self.get_user()

    def get_user(self):
        bookmark = models.Bookmark.objects.filter(pk__in=self.documents).first()
        if bookmark is None:
            raise ValueError
        return bookmark.user

    def split_documents(self) -> tuple[list[int], list[int]]:
        """Split documents into related and not related to old documents graph"""
        # TODO use dfs -> flatten -> set (all - related)
        related_indexes = []
        not_related_indexes = []
        for index, row in enumerate(self.intersected_similarity):
            if max(row) > 0.2:
                related_indexes.append(index)
            else:
                not_related_indexes.append(index)

        neighbors = []
        for index in related_indexes:
            for i in not_related_indexes:
                if self.similarity_matrix[index][i] > 0.2 and i not in related_indexes:
                    related_indexes.append(i)
                    neighbors.append(i)
        
        not_related_indexes = list(set(not_related_indexes) - set(neighbors))
        return related_indexes, not_related_indexes

    def group_to_documents(self, group: list[int]) -> list[str]:
        return [self.documents[index] for index in group]

    def group_to_sub_matrix(self, group: list[int]) -> list[list[float]]:
        return self.similarity_matrix[np.ix_(group, group)]

    def locate_leaf(self, doc: int, similar_docs : list[tuple[int, float]]):
        query = Q()
        for other_doc, similarity in similar_docs:
            query |= Q(bookmarks__id=other_doc, threshold__lte=similarity)

        created = False
        leaf = models.GraphNode.objects.filter(query).order_by('-threshold').distinct().first()
        
        if not leaf:
            nearest_doc_id, similarity = max(similar_docs, key=lambda x: x[1])
            nearest_node = models.GraphNode.objects.filter(bookmarks__id=nearest_doc_id).distinct().first()
            if nearest_node is None:
                raise ValueError('nearest node is None')

            nearest_parent = nearest_node.parent
            while nearest_parent and nearest_parent.threshold > similarity:
                nearest_parent = nearest_parent.parent
                
            if nearest_parent is None:
                raise ValueError('nearest parent is None')

            created = True
            leaf = models.GraphNode.objects.create(
                user=self.user,
                parent=nearest_parent,
                threshold=similarity, # TODO threshold should be divisible by threshold_step
                bookmarks_count=1,
                is_leaf=True,
                similarity_matrix=[]
            )
        
        return leaf , created

    def merge_to_old_graph(self, group: list[int]):
        # TODO make sure order of the group is correct
        documents_ids = self.group_to_documents(group)
        similarity_matrix = self.group_to_sub_matrix(group)
        intersected_similarity = self.intersected_similarity[np.ix_(group, group)]
        leaf_nodes = self.user.nodes.filter(is_leaf=True, bookmarks__isnull=False)

        indirect_documents = []
        direct_documents = []
        # documents related to old graph
        for doc, similarities in zip(documents_ids, intersected_similarity):
            old_docs = list(filter(lambda x: x[1] >= 0.2, zip(self.old_documents, similarities)))
            
            if not old_docs:
                # not a direct relation
                indirect_documents.append(doc)
                continue
            else:
                direct_documents.append(doc)
            
            old_docs_ids = list(map(lambda x: x[0], old_docs))
            related_leafs = leaf_nodes.filter(bookmarks__in=old_docs_ids).distinct().values_list('path', flat=True)
            related_leafs_roots = set(map(lambda x: x and x.split('.', 1)[0], related_leafs))
            if len(related_leafs_roots) > 0:
                # TODO merge roots
                # 1- has no root with 0 threshold -> create
                # 2- has root with 0 threshold -> use it
                # 3- has mode than one root with 0 threshold -> keep only one and delete others
                pass

            leaf, created = self.locate_leaf(doc, old_docs)
            # TODO update similarity matrix
            leaf.bookmarks.add(models.Bookmark.objects.get(pk=doc))
        for direct_doc in direct_documents:
            direct_idx = documents_ids.index(direct_doc)
            for indirect_doc in indirect_documents:
                indirect_idx = documents_ids.index(indirect_doc)
                similarity = similarity_matrix[direct_idx][indirect_idx]
                if similarity > 0.2:
                    leaf, created = self.locate_leaf(doc, [(direct_doc, similarity)])
                    # TODO update similarity matrix
                    leaf.bookmarks.add(models.Bookmark.objects.get(pk=doc))
                    indirect_documents.remove(indirect_doc)
                    break

        # while indirect_documents:
        #     doc = indirect_documents.pop(0)
        #     doc_index = documents_ids.index(doc)
        #     similarities = similarity_matrix[doc_index]
            
        #     # get nearest document that also related to old graph
        #     nearest_docs = list(filter(
        #         lambda x: x[0] in direct_documents and x[1] >= 0.2, 
        #         zip(documents_ids, similarities)
        #     ))
            
        #     if not nearest_docs:
        #         indirect_documents.append(doc)
        #         continue
        #     else:
        #         direct_documents.append(doc)

        #     # then find its leaf
        #     # then route it according to ist similarity and leaf threshold
        #     leaf, created = self.locate_leaf(doc, nearest_docs)
        #     # TODO update similarity matrix
        #     leaf.bookmarks.add(models.Bookmark.objects.get(pk=doc))

    def run(self):
        related_indexes, not_related_indexes = self.split_documents()
        # handle not related normally
        if not_related_indexes:
            WordGraphBuilder(
                documents=self.group_to_documents(not_related_indexes),
                similarity_matrix=self.group_to_sub_matrix(not_related_indexes),
            ).build()

        self.merge_to_old_graph(related_indexes)

