from django.db.models import Q
from django_filters import rest_framework as filters
from django_filters.filters import BaseInFilter

from App import models


class TagFilter(filters.FilterSet):
    name = filters.CharFilter("name", lookup_expr="icontains")
    bookmark = filters.NumberFilter("bookmarks__id")

    node = filters.NumberFilter("nodes__id")

    exclude = filters.CharFilter(method="filter_exclude")

    def filter_exclude(self, queryset, name, value):
        return queryset.exclude(name__icontains=value)

    class Meta:
        model = models.Tag
        fields = ["name"]


class ListFilter(BaseInFilter, filters.CharFilter):
    pass


class BookmarkFilter(filters.FilterSet):
    process_status = filters.NumberFilter("process_status")

    file = filters.NumberFilter("parent_file_id")

    tag = filters.NumberFilter("tags__id")
    tag_name = filters.CharFilter("tags__name", lookup_expr="icontains")

    node = filters.NumberFilter("nodes__path", lookup_expr="contains")
    exclude_node = filters.NumberFilter(
        "nodes__path", lookup_expr="contains", exclude=True
    )

    websites = ListFilter(field_name="website_id", lookup_expr="in")
    exclude_websites = ListFilter(
        field_name="website_id", lookup_expr="in", exclude=True
    )

    topics = ListFilter(field_name="tags__id", lookup_expr="in")
    exclude_topics = ListFilter(field_name="tags__id", lookup_expr="in", exclude=True)

    seen = filters.BooleanFilter("history", lookup_expr="isnull", exclude=True)
    dead = filters.BooleanFilter("scrapes__status_code", method="filter_dead")

    def filter_dead(self, queryset, name, value):
        lookup = Q(scrapes__status_code__gt=300) & Q(scrapes__status_code__lt=500)
        if value:
            return queryset.filter(lookup)

        ids = queryset.filter(lookup).values_list("id", flat=True)
        return queryset.filter(~Q(id__in=ids))

    class Meta:
        model = models.Bookmark
        fields = ["process_status", "tags", "parent_file"]
