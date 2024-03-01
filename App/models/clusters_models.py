import json
import numpy as np

from django.db import models
from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from django.core.validators import FileExtensionValidator
from django.core.files.base import ContentFile

from common.utils.file_utils import random_filename


class Cluster(models.Model):
    """Generated by ML model or Equation or whatever
    Grouping bookmarks blindly without knowing the relation
    """

    # Relations
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name='clusters'
    )
    bookmarks = models.ManyToManyField('App.Bookmark', related_name='clusters')

    # Required , can be null and user can set it
    # if it null then it will be calculated using the highest tag
    name = models.CharField(max_length=128)
    correlation = models.FloatField(default=0.0)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def tags(self):
        tags = Tag.objects.filter(
            bookmarks__in=self.bookmarks.all()).distinct()
        return tags

    @property
    def general_words_vector(self):
        general_vector = {}
        for b in self.bookmarks.all():
            for word, weight in b.word_vector.items():
                general_vector.setdefault(word, 0)
                general_vector[word] += weight

        return general_vector

    def get_absolute_url(self):
        return reverse("app:cluster-detail", kwargs={"pk": self.pk})


class Tag(models.Model):
    '''Tag is a stored operation for words table
    weight = sum([word.weight for word in words])
    name = word.name
    bookmarks = bookmarks that related to this word
    alias_name = name by the user
    '''
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name='tags'
    )
    # TODO bookmarks should be RCs
    bookmarks = models.ManyToManyField(
        'App.Bookmark', blank=True, related_name='tags')

    # Required
    name = models.CharField(max_length=128)

    # Optional
    alias_name = models.CharField(max_length=128, blank=True, null=True)

    # Computed
    weight = models.PositiveSmallIntegerField(default=0)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'name')

    def __str__(self):
        return f'{self.pk} - {self.name} = {self.weight}'

    def get_absolute_url(self):
        return reverse("app:tag-detail", kwargs={"pk": self.pk})


class SimilarityMatrix(models.Model):
    user = models.OneToOneField(
        get_user_model(), on_delete=models.CASCADE, related_name='similarity_matrix'
    )

    file = models.FileField(
        upload_to='similarity-matrix/',
        validators=[FileExtensionValidator(['json'])])

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)  # Call the real save() method

    @property
    def bookmarks(self):
        from App.models import Bookmark
        return self.user.bookmarks.filter(
            process_status=Bookmark.ProcessStatus.CLUSTERED.value
        )

    @property
    def to_type(self):
        from . import WordWeight
        from App.types import SimilarityMatrixType

        document_ids, vectors = WordWeight.word_vectors(self.bookmarks)

        return SimilarityMatrixType.load(
            vectors=vectors,
            document_ids=document_ids,
            path=self.file.path
        )

    def update_matrix(self, similarity_matrix: np.ndarray):
        with self.file.open('w') as f:
            f.write(json.dumps(similarity_matrix.tolist()))
        return True

    @classmethod
    def get_object(cls, user):
        try:
            return cls.objects.get(user=user)
        except cls.DoesNotExist:
            path = random_filename(cls.file.field.upload_to, 'json')
            filename = path.split('/')[-1]
            content_file = ContentFile(b"{}", name=filename)

            return cls.objects.create(user=user, file=content_file)
