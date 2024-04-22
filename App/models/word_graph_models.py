from django.db import models
from django.contrib.auth import get_user_model


class WordGraphNode(models.Model):
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name='nodes')
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, related_name='children')

    tags = models.ManyToManyField('App.Tag', related_name='nodes', blank=True)
    bookmarks = models.ManyToManyField(
        'App.Bookmark', related_name='nodes', blank=True)
    bookmarks_count = models.PositiveSmallIntegerField(default=0)

    path = models.CharField(max_length=1024, blank=True,
                            null=True, db_index=True)
    threshold = models.FloatField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs) -> None:
        if self.pk is None and self.parent:
            path_list = []
            if self.parent.path:
                path_list.append(self.parent.path)
            path_list.append(self.parent.pk)

            self.path = '.'.join(map(str, path_list))
        return super().save(*args, **kwargs)

    @property
    def leafs(self):
        cls = self._meta.model
        path = self.path
        if self.path is None:
            path = f'{self.pk}'
        return cls.objects.filter(path__startswith=path, bookmarks__isnull=False).distinct()

    def keywords(self):
        return self.tags.all().values_list('name', flat=True)

    def get_bookmarks(self):
        from App.models import Bookmark

        if self.bookmarks.exists():
            bookmarks = self.bookmarks.all()
        else:
            bookmarks = Bookmark.objects.filter(
                nodes__in=self.leafs).distinct()
        return bookmarks
