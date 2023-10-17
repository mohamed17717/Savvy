from django.db import models
from django.contrib.auth import get_user_model


class DocumentCluster(models.Model):
    # Relations
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name='clusters'
    )
    bookmarks = models.ManyToManyField('App.Bookmark', related_name='clusters')

    # Required
    name = models.CharField(max_length=128)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def general_words_vector(self):
        general_vector = {}
        for b in self.bookmarks.all():
            for word, weight in b.word_vector.items():
                general_vector.setdefault(word, 0)
                general_vector[word] += weight

        return general_vector


class ClusterTag(models.Model):
    # Relations
    cluster = models.ForeignKey(
        'App.DocumentCluster', on_delete=models.CASCADE, related_name='tags'
    )
    # Required
    name = models.CharField(max_length=64)

    # Defaults
    show = models.BooleanField(default=True)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
