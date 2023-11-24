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

    def refresh_labels(self):
        general_vector = self.general_words_vector

        # sort words desc on its general weight
        words = sorted(general_vector.keys(), key=lambda i: -general_vector[i])

        # 2/3 of words consider tops but less than 10
        MAX_WORDS_COUNT = 10
        top_words_count = len(words) * 2 // 3
        top_words_count = min(MAX_WORDS_COUNT, top_words_count)
        top_words = words[:top_words_count]

        # store labels
        # TODO words with be duplicated and this is not efficient relation
        # solve it
        ClusterTag.objects.bulk_create([
            ClusterTag(cluster=self, name=word) for word in top_words
        ])


class ClusterTag(models.Model):
    # Relations
    cluster = models.ForeignKey(
        'App.DocumentCluster', on_delete=models.CASCADE, related_name='tags'
    )
    # Required
    # TODO make it 64 when cleaner work fine
    name = models.CharField(max_length=2048)

    # Defaults
    show = models.BooleanField(default=True)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
