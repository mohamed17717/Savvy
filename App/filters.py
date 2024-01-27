import json

from django_filters import rest_framework as filters
from App import models


class TagFilter(filters.FilterSet):
    name = filters.CharFilter('name', lookup_expr='icontains')

    class Meta:
        model = models.Tag
        fields = ['name']


class ClusterFilter(filters.FilterSet):
    name = filters.CharFilter('name', lookup_expr='icontains')
    correlation_min = filters.NumberFilter('correlation', lookup_expr='gte')
    correlation_max = filters.NumberFilter('correlation', lookup_expr='lte')

    class Meta:
        model = models.Cluster
        fields = ['name', 'correlation']


class BookmarkFilter(filters.FilterSet):
    class Meta:
        model = models.Bookmark
        fields = []
