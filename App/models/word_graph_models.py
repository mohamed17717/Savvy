from django.contrib.auth import get_user_model
from django.db import models


class GraphNode(models.Model):
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="nodes"
    )
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, related_name="children"
    )

    name = models.CharField(max_length=256, blank=True, null=True)

    tags = models.ManyToManyField("App.Tag", related_name="nodes", blank=True)
    bookmarks = models.ManyToManyField("App.Bookmark", related_name="nodes", blank=True)
    bookmarks_count = models.PositiveSmallIntegerField(default=0)

    path = models.CharField(max_length=1024, blank=True, null=True, db_index=True)
    threshold = models.FloatField(blank=True, null=True)

    is_leaf = models.BooleanField(default=False)  # has no children
    # merged of small nodes that contain only 1, 2 or 3 bookmarks
    is_sharded_islands = models.BooleanField(default=False)
    similarity_matrix = models.JSONField(blank=True, null=True)  # only for leafs

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    CREATOR = None

    def __str__(self):
        return self.name

    def calculate_path(self) -> list[str]:
        path = f"{self.pk}"
        if self.parent:
            path = self.parent.path + "." + path

        self.path = path
        return ["path"]

    def post_create(self):
        return self.calculate_path()

    def save(self, *args, **kwargs) -> None:
        created = not self.pk

        result = super().save(*args, **kwargs)

        if created:
            update_fields = self.post_create()
            self.save(update_fields=update_fields)

        return result

    @property
    def leafs(self):
        cls = self._meta.model
        path = self.path
        if self.path is None:
            path = f"{self.pk}"
        return cls.objects.filter(
            path__startswith=path, bookmarks__isnull=False
        ).distinct()

    def keywords(self):
        return self.tags.all().values_list("name", flat=True)

    def get_bookmarks(self):
        from App.models import Bookmark

        if self.bookmarks.exists():
            bookmarks = self.bookmarks.all()
        else:
            bookmarks = Bookmark.objects.filter(nodes__in=self.leafs).distinct()
        return bookmarks

    @classmethod
    def centralized_creator(cls):
        from common.utils.model_utils import CentralizedBulkCreator

        if cls.CREATOR is None:
            cls.CREATOR = CentralizedBulkCreator(cls, ["bookmarks", "tags"])
        return cls.CREATOR
