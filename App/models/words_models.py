from django.db import models
from django.contrib.auth import get_user_model

from App.types import WordVectorType
from App.managers import SignalsCustomManager

User = get_user_model()


class DocumentWordWeight(models.Model):
    # Relations
    # TODO in future -> this field become generic relation
    # to relate with (bookmark / youtube / linkedin / etc...)
    bookmark = models.ForeignKey(
        'App.Bookmark', on_delete=models.CASCADE, related_name='words_weights')

    # Required
    # TODO make it 64 when cleaner work fine
    word = models.CharField(max_length=2048)
    weight = models.PositiveSmallIntegerField()

    important = models.BooleanField(default=False)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SignalsCustomManager()

    def __str__(self):
        return f'{self.word} - {self.weight} <DOC: {self.bookmark}>'

    @classmethod
    def word_vectors(cls, bookmarks) -> dict[int, WordVectorType]:
        words_qs = cls.objects.filter(bookmark__in=bookmarks, important=True)
        words_qs = words_qs.values_list('bookmark_id', 'word', 'weight')

        document_vectors = {}  # id: {word: weight}
        for doc_id, word, weight in words_qs:
            document_vectors.setdefault(doc_id, WordVectorType())
            document_vectors[doc_id][word] = weight

        return list(document_vectors.keys()), list(document_vectors.values())
