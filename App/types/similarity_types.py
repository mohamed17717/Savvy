class WordVectorType(dict):
    """This class type represent a dict of `word` to its `weight`"""

    def weight_vector(self, unique_words: tuple[str]) -> tuple[int]:
        return tuple(self.get(word, 0) for word in unique_words)
