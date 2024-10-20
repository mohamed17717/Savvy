from django.contrib.auth import get_user_model
from django.contrib.postgres.aggregates import ArrayAgg
from django.db import models
from django.db.models import Sum
from django.shortcuts import reverse

from App import managers

User = get_user_model()


class Tag(models.Model):
    """Tag is a stored operation for words table
    name = word.name
    bookmarks = bookmarks that related to this word
    """

    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="tags"
    )
    bookmarks = models.ManyToManyField("App.Bookmark", blank=True, related_name="tags")
    bookmarks_count = models.PositiveSmallIntegerField(default=0, db_index=True)

    # Required
    name = models.CharField(max_length=128)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = managers.TagManager()

    class Meta:
        unique_together = ("user", "name")

    def __str__(self):
        return f"{self.pk} - {self.name}"

    def get_absolute_url(self):
        return reverse("app:tag-detail", kwargs={"pk": self.pk})
