from django.db import models
from django.contrib.auth import get_user_model

from App.types import WordVectorType

User = get_user_model()


class WordWeight(models.Model):
    # Relations
    bookmark = models.ForeignKey(
        'App.Bookmark', on_delete=models.CASCADE, related_name='words_weights')

    # Required
    word = models.CharField(max_length=64, db_index=True)
    weight = models.PositiveSmallIntegerField()

    important = models.BooleanField(default=False)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.word} - {self.weight} <DOC: {self.bookmark}>'

    @classmethod
    def word_vectors(cls, bookmarks) -> tuple[list[int], list[WordVectorType]]:
        # TODO return vector for each bookmark
        words_qs = cls.objects.filter(bookmark__in=bookmarks, important=True)
        words_qs = words_qs.values_list('bookmark_id', 'word', 'weight')

        document_vectors = {}  # id: {word: weight}
        for doc_id, word, weight in words_qs:
            document_vectors.setdefault(doc_id, WordVectorType())
            document_vectors[doc_id][word] = weight

        return list(document_vectors.keys()), list(document_vectors.values())
