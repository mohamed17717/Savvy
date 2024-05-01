from django_filters import rest_framework as filters

from App import models


class TagFilter(filters.FilterSet):
    name = filters.CharFilter('name', lookup_expr='icontains')
    bookmark = filters.NumberFilter('bookmarks__id')

    node = filters.NumberFilter('nodes__id')

    exclude = filters.CharFilter(method='filter_exclude')

    def filter_exclude(self, queryset, name, value):
        return queryset.exclude(
            name__icontains=value, alias_name__icontains=value
        )

    class Meta:
        model = models.Tag
        fields = ['name']


class ClusterFilter(filters.FilterSet):
    name = filters.CharFilter('name', lookup_expr='icontains')
    correlation_min = filters.NumberFilter('correlation', lookup_expr='gte')
    correlation_max = filters.NumberFilter('correlation', lookup_expr='lte')
    bookmark = filters.NumberFilter('bookmarks__id')

    exclude = filters.CharFilter(method='filter_exclude')

    def filter_exclude(self, queryset, name, value):
        return queryset.exclude(
            name__icontains=value,
        )

    class Meta:
        model = models.Cluster
        fields = ['name', 'correlation']


class BookmarkFilter(filters.FilterSet):
    status = filters.NumberFilter('user_status')
    process_status = filters.NumberFilter('process_status')

    file = filters.NumberFilter('parent_file_id')

    tag = filters.NumberFilter('tags__id')
    tag_name = filters.CharFilter('tags__name', lookup_expr='icontains')

    cluster = filters.NumberFilter('clusters__id')

    node = filters.NumberFilter('nodes__path', lookup_expr='icontains')

    exclude = filters.CharFilter(method='filter_exclude')

    def filter_exclude(self, queryset, name, value):
        return queryset.exclude(
            words_weights__word__icontains=value
        )

    class Meta:
        model = models.Bookmark
        fields = ['user_status', 'process_status', 'tags', 'clusters', 'parent_file']
