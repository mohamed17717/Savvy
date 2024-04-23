import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from App import models


class WordGraphModifier:
    # NOT WORKING
    def __init__(self, documents, similarity_matrix, graphed_documents):
        self.documents = documents
        self.similarity_matrix = similarity_matrix
        self.graphed_documents = graphed_documents
        self.intersection_matrix = None
        
        self.calculate_intersection_matrix()

    def calculate_intersection_matrix(self):
        _, graphed_vectors = models.WordWeight.word_vectors(self.graphed_documents)
        _, documents_vectors = models.WordWeight.word_vectors(self.documents)

        def unique_words(vectors):
            words = set()
            for v in vectors:
                words.update(v.keys())
            return words
        
        def weight_matrix(vectors, words):
            matrix = np.zeros((len(vectors), len(words)))
            for i, v in enumerate(vectors):
                for j, word in enumerate(words):
                    matrix[i][j] = v.get(word, 0)
            return matrix

        words = unique_words([*graphed_vectors, *documents_vectors])

        self.intersection_matrix = cosine_similarity(
            weight_matrix(graphed_vectors, words),
            weight_matrix(documents_vectors, words)
        )

    def remove_document(self, doc_index):
        self.documents.pop(doc_index)
        self.similarity_matrix = np.delete(self.similarity_matrix, doc_index, axis=0)
        self.similarity_matrix = np.delete(self.similarity_matrix, doc_index, axis=1)
        self.intersection_matrix = np.delete(self.intersection_matrix, doc_index, axis=0)
        self.intersection_matrix = np.delete(self.intersection_matrix, doc_index, axis=1)

    def modify(self):
        ...


class MergeGraphs:
    # NOT WORKING
    def __init__(self, graph1, graph2):
        self.original_graph = graph1
        self.sub_graph = graph2

    def is_similar_nodes(self, node1, node2):
        _, node1_vectors = models.WordWeight.word_vectors(node1.bookmarks.all())
        _, node2_vectors = models.WordWeight.word_vectors(node2.bookmarks.all())

        def unique_words(vectors):
            words = set()
            for v in vectors:
                words.update(v.keys())
            return words
        
        def node_vector(vectors, words):
            vector = [0] * len(words)
            weights = {}
            for v in vectors:
                for word, weight in v.items():
                    weights[word] = weights.get(word, 0) + weight
            for i, word in enumerate(words):
                vector[i] = weights.get(word, 0)
            return [vector]

        words = unique_words([*node1_vectors, *node2_vectors])
        similarity = cosine_similarity(
            node_vector(node1_vectors, words),
            node_vector(node2_vectors, words)
        )[0][0]
        
        return similarity > max(node1.threshold, node2.threshold)

    def leaf_to_leaf(self, sub, original):
        original.bookmarks.add(*sub.bookmarks.all())

        sub_parent = sub.parent
        sub.delete()
        while sub_parent and sub_parent.children.exists() is False:
            grand_parent = sub_parent.parent
            sub_parent.delete()
            sub_parent = grand_parent

        # TODO if original node bookmarks count exceeded the limit
        # split it into two nodes
        # TODO create new field that hold the similarity matrix and documents ids

    def leaf_to_node(self, sub, original):
        # TODO compare sub to original children and add leaf to most relevant recursively
        # NOTE most relevant is by comparing the similarity by node.threshold
        # if no most relevant then add leaf as a sibling by changing its parent
        # otherwise its relevant to a leaf merge them using self.leaf_to_leaf()
        pass

    
    def node_to_leaf(self, sub, original):
        # TODO add node as a sibling then apply self.leaf_to_node() between them
        pass

    def node_to_node(self, sub, original):
        # TODO create new instance of merge graph between children of each node
        pass

    def merge(self):
        # TODO merge should be to most similar no all nodes
        for sub_node in self.sub_graph:
            for original_node in self.original_graph:
                is_similar = self.is_similar_nodes(sub_node, original_node)
                if not is_similar:
                    continue

                if sub_node.is_leaf and original_node.is_leaf:
                    self.leaf_to_leaf(sub_node, original_node)

                elif sub_node.is_leaf and not original_node.is_leaf:
                    self.leaf_to_node(sub_node, original_node)

                elif not sub_node.is_leaf and original_node.is_leaf:
                    self.node_to_leaf(sub_node, original_node)
                
                elif not sub_node.is_leaf and not original_node.is_leaf:
                    self.node_to_node(sub_node, original_node)
                
