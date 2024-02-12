import copy

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class WordVectorType(dict):
    """This class type represent a dict of `word` to its `weight`"""

    def weight_vector(self, unique_words: tuple[str]) -> tuple[int]:
        return tuple(self.get(word, 0) for word in unique_words)


class SimilarityMatrixType:
    """This class type represent an object that hold all data about similarity calculations
    Like:
        - similarity matrix
        - ordered documents
        - ordered unique words
    """

    def __init__(
        self,
        vectors: list[WordVectorType],  # table of data
        document_ids: list[int],  # y_axis
        unique_words: list[str] = None,  # x_axis
        similarity_matrix: np.ndarray = None  # relation between documents base on words
    ) -> None:
        self.vectors = vectors
        self.document_ids = document_ids
        self._unique_words = unique_words
        self._similarity_matrix = similarity_matrix

    @property
    def unique_words(self) -> set:
        def calculate():
            words = set()
            for v in self.vectors:
                words.update(v.keys())
            return words

        return self._unique_words or calculate()

    def weight_matrix(self, unique_words=None):
        if unique_words is None:
            unique_words = self.unique_words
        return tuple(v.weight_vector(unique_words) for v in self.vectors)

    @property
    def similarity_matrix(self) -> np.ndarray:
        def calculate():
            matrix = cosine_similarity(self.weight_matrix())
            return np.ceil(matrix*100)/100

        return self._similarity_matrix or calculate()

    def __repr__(self):
        return self.similarity_matrix.__repr__()

    def __add__(self, other: 'SimilarityMatrixType') -> 'SimilarityMatrixType':
        if not isinstance(other, SimilarityMatrixType):
            raise TypeError(f"Can't add {type(other)} to {type(self)}")

        # TODO if needed // remove duplicated words and do the operations normally
        if set(self.document_ids).intersection(other.document_ids):
            raise ValueError(
                "Can't add two SimilarityMatrixType with same document_ids")

        # Combine dimensions
        unique_words = tuple(set(self.unique_words).add(other.unique_words))
        intersect_similarity = cosine_similarity(
            other.weight_matrix(unique_words), self.weight_matrix(unique_words)
        )

        similarity_matrix = copy.deepcopy(self.similarity_matrix)
        similarity_matrix = np.vstack(
            (similarity_matrix, intersect_similarity))

        intersect_similarity = np.rot90(intersect_similarity, k=1)[::-1]
        intersect_similarity = np.vstack(
            (intersect_similarity, other.similarity_matrix))

        similarity_matrix = np.hstack(
            (similarity_matrix, intersect_similarity))

        return SimilarityMatrixType(
            vectors=[*self.vectors, *other.vectors],
            document_ids=[*self.document_ids, *other.document_ids],
            unique_words=unique_words,
            similarity_matrix=similarity_matrix
        )

    def store(self, path: str) -> str:
        """store data in this directory and return full path

        Args:
            path (str): path to directory

        Returns:
            str: full path
        """
        np.save(path, self.similarity_matrix)
        return path

    @classmethod
    def load(cls, vectors: list[WordVectorType], document_ids: list[int], path: str) -> 'SimilarityMatrixType':
        return cls(
            vectors=vectors,
            document_ids=document_ids,
            similarity_matrix=np.load(path)
        )
