import math

from django.db.models import Prefetch, QuerySet

from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.generics import ListAPIView

from App import serializers, filters, models

from common.utils.drf.viewsets import CRDLViewSet, RULViewSet
from common.utils.math_utils import dynamic_number_boundaries


class BookmarkFileAPI(CRDLViewSet):
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = serializers.BookmarkFileSerializer

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return models.BookmarkFile.objects.none()

        return self.request.user.bookmark_files.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ClusterAPI(RULViewSet):
    filterset_class = filters.ClusterFilter
    serializer_class = serializers.ClusterSerializer

    def get_serializer_class(self):
        serializer_class = self.serializer_class

        if self.action == 'update' or self.action == 'partial_update':
            serializer_class = serializers.ClusterSerializer.ClusterUpdate
        elif self.action == 'list':
            serializer_class = serializers.ClusterSerializer.ClusterDetails
        elif self.action == 'retrieve':
            serializer_class = serializers.ClusterSerializer.ClusterDetails

        return serializer_class

    def _prefetch(self, qs: QuerySet) -> QuerySet:
        tags_qs = self.request.user.tags.all().order_by('-weight')
        tags_prefetch = Prefetch('bookmarks__tags', queryset=tags_qs)

        return qs.prefetch_related('bookmarks', tags_prefetch)

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return models.Cluster.objects.none()

        qs = self.request.user.clusters.all()

        if self.action == 'update' or self.action == 'partial_update':
            pass
        elif self.action == 'list':
            qs = qs.order_by('-correlation')
            qs = self._prefetch(qs)
        elif self.action == 'retrieve':
            qs = self._prefetch(qs)

        return qs


class ClusterFullListAPI(ListAPIView):
    filterset_class = filters.ClusterFilter
    serializer_class = serializers.ClusterSerializer.ClusterFullDetails
    pagination_class = None

    def _prefetch(self, qs: QuerySet) -> QuerySet:
        tags_qs = self.request.user.tags.all().order_by('-weight')
        tags_prefetch = Prefetch('bookmarks__tags', queryset=tags_qs)

        return qs.prefetch_related('bookmarks', tags_prefetch)

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return models.Cluster.objects.none()

        qs = self.request.user.clusters.all().order_by('-correlation')
        qs = self._prefetch(qs)

        return qs


class BookmarkAPI(RULViewSet):
    filterset_class = filters.BookmarkFilter
    serializer_class = serializers.BookmarkSerializer

    def get_serializer_class(self):
        serializer_class = self.serializer_class

        if self.action == 'update' or self.action == 'partial_update':
            serializer_class = serializers.BookmarkSerializer.BookmarkUpdate
        elif self.action == 'list':
            pass
        elif self.action == 'retrieve':
            serializer_class = serializers.BookmarkSerializer.BookmarkDetails

        return serializer_class

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return models.Bookmark.objects.none()

        qs = self.request.user.bookmarks.all()

        if self.action == 'update' or self.action == 'partial_update':
            pass
        elif self.action == 'list':
            pass
        elif self.action == 'retrieve':
            pass

        return qs


class TagAPI(RULViewSet):
    pagination_class = None
    serializer_class = serializers.TagSerializer

    def get_serializer_class(self):
        serializer_class = self.serializer_class

        if self.action == 'update' or self.action == 'partial_update':
            serializer_class = serializers.TagSerializer.TagUpdate
        elif self.action == 'list':
            serializer_class = serializers.TagSerializer.TagList
        elif self.action == 'retrieve':
            serializer_class = serializers.TagSerializer.TagDetails

        return serializer_class

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return models.Tag.objects.none()

        qs = self.request.user.tags.all()

        if self.action == 'update' or self.action == 'partial_update':
            pass
        elif self.action == 'list':
            limit = math.ceil(qs.count() * 0.1)
            limit = dynamic_number_boundaries(limit, 10, 50)
            qs = qs.order_by('-weight')[:limit]
        elif self.action == 'retrieve':
            qs = qs.prefetch_related('bookmarks')

        return qs


class TagListAPI(ListAPIView):
    serializer_class = serializers.TagSerializer.TagList
    filterset_class = filters.TagFilter

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return models.Tag.objects.none()
        return self.request.user.tags.all().order_by('-weight')
