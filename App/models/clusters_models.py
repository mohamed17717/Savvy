from django.contrib.auth import get_user_model
from django.contrib.postgres.aggregates import ArrayAgg
from django.db import models
from django.db.models import Sum
from django.shortcuts import reverse

from App import managers


class Tag(models.Model):
    """Tag is a stored operation for words table
    weight = sum([word.weight for word in words])
    name = word.name
    bookmarks = bookmarks that related to this word
    alias_name = name by the user
    """

    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="tags"
    )
    bookmarks = models.ManyToManyField("App.Bookmark", blank=True, related_name="tags")
    bookmarks_count = models.PositiveSmallIntegerField(default=0, db_index=True)

    # Required
    name = models.CharField(max_length=128)

    # Optional
    alias_name = models.CharField(max_length=128, blank=True, null=True)

    # Computed
    weight = models.PositiveIntegerField(default=0)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = managers.TagManager()

    class Meta:
        unique_together = ("user", "name")

    def __str__(self):
        return f"{self.pk} - {self.name} = {self.weight}"

    def get_absolute_url(self):
        return reverse("app:tag-detail", kwargs={"pk": self.pk})

    @classmethod
    def update_tags_with_new_bookmarks(cls, bookmarks_ids: list[int]):
        from App.models import Bookmark, WordWeight

        bookmarks = Bookmark.all_objects.filter(id__in=bookmarks_ids).exclude(
            tags__isnull=False
        )

        # make sure this bookmarks has no tags
        if not bookmarks.exists():
            raise ValueError("Bookmarks has tags")

        user = bookmarks.first().user
        # get words
        words_qs = (
            WordWeight.objects.filter(bookmark_id__in=bookmarks_ids, important=True)
            .values("word")
            .annotate(total_weight=Sum("weight"), bookmark_ids=ArrayAgg("bookmark"))
        )
        words = set(words_qs.values_list("word", flat=True))
        words_map = {w["word"]: w for w in words_qs}

        # Update existing tags
        existing_tags = user.tags.filter(name__in=words)
        for tag in existing_tags:
            tag.weight += words_map[tag.name]["total_weight"]
            tag.bookmarks_count += len(set(words_map[tag.name]["bookmark_ids"]))
        cls.objects.bulk_update(
            existing_tags, ["weight", "bookmarks_count"], batch_size=250
        )

        # Create new tags
        existing_tag_names = set(existing_tags.values_list("name", flat=True))
        new_tag_names = words - existing_tag_names

        user = Bookmark.objects.filter(pk__in=bookmarks_ids).first().user

        new_tags = [
            cls(
                name=name,
                weight=words_map[name]["total_weight"],
                user=user,
                bookmarks_count=len(set(words_map[name]["bookmark_ids"])),
            )
            for name in new_tag_names
        ]
        new_tags = cls.objects.bulk_create(new_tags, batch_size=250)

        # Create relation between tags and bookmarks
        all_tags = [*existing_tags, *new_tags]
        relation_model = cls.bookmarks.through
        relations = []

        for tag in all_tags:
            relations.extend(
                [
                    relation_model(bookmark_id=bookmark_id, tag_id=tag.pk)
                    for bookmark_id in set(words_map[tag.name]["bookmark_ids"])
                ]
            )

        relation_model.objects.bulk_create(relations, batch_size=250)

        return len(all_tags)
