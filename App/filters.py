import json

from django_filters import rest_framework as filters
from App import models


class TagFilter(filters.FilterSet):
    name = filters.CharFilter('name', lookup_expr='icontains')
    bookmark = filters.NumberFilter('bookmarks__id')

    class Meta:
        model = models.Tag
        fields = ['name']


class ClusterFilter(filters.FilterSet):
    name = filters.CharFilter('name', lookup_expr='icontains')
    correlation_min = filters.NumberFilter('correlation', lookup_expr='gte')
    correlation_max = filters.NumberFilter('correlation', lookup_expr='lte')
    bookmark = filters.NumberFilter('bookmarks__id')

    class Meta:
        model = models.Cluster
        fields = ['name', 'correlation']


class BookmarkFilter(filters.FilterSet):
    status = filters.NumberFilter('status')
    
    file = filters.NumberFilter('parent_file_id')

    crawled = filters.BooleanFilter('crawled')

    tag = filters.NumberFilter('tags__id')
    tag_name = filters.CharFilter('tags__name', lookup_expr='icontains')

    cluster = filters.NumberFilter('clusters__id')

    class Meta:
        model = models.Bookmark
        fields = ['status', 'tags', 'clusters', 'parent_file', 'crawled']
