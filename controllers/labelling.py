

class ClusterLabelBuilder:
    MAX_LABEL_NUMBER = 6

    def __init__(self, cluster: list[dict]):
        self.cluster = cluster

    def __merge_docs(self) -> dict:
        cluster_words = {}

        for doc in self.cluster:
            for word, weight in doc.items():
                cluster_words.setdefault(word, 0)
                cluster_words[word] += weight
                    
        return cluster_words

    def __order_words(self, cluster_words: dict) -> list[str]:
        order_by = lambda item: cluster_words[item]

        ordered_words = sorted(cluster_words.keys(), key=order_by)
        ordered_words = reversed(ordered_words)
        ordered_words = list(ordered_words)
        
        return ordered_words

    def __extract_top_words(self, ordered_words, max_number: int|None= None):
        half_index = len(ordered_words) // 2
        if max_number is not None:
            half_index = min(max_number, half_index)

        return ordered_words[:half_index]

    def build(self):
        cluster_words = self.__merge_docs()
        ordered_words = self.__order_words(cluster_words)
        top_words = self.__extract_top_words(ordered_words, self.MAX_LABEL_NUMBER)
        
        return top_words

    def __ai_score(self, text, labels):
        from transformers import pipeline

        pipe = pipeline(model="facebook/bart-large-mnli")
        res = pipe(text, candidate_labels=labels)

        for i in zip(res['labels'], zip(res['scores'])):
            print(i)
        

