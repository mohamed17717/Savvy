import json

from django_filters import rest_framework as filters
from App import models


class TagFilter(filters.FilterSet):
    name = filters.CharFilter('name', lookup_expr='icontains')

    class Meta:
        model = models.Tag
        fields = ['name']
