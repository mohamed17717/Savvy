import math

from django.db.models import Prefetch, QuerySet, Count
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect

from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from App import serializers, filters, models

from common.utils.drf.viewsets import CRDLViewSet, RULViewSet
from common.utils.math_utils import minmax
from realtime.common.jwt_utils import JwtManager


class BookmarkFileAPI(CRDLViewSet):
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = serializers.BookmarkFileSerializer

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        JwtManager.inject_cookie(response, data={'user_id': request.user.id})

        return response

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return models.BookmarkFile.objects.none()

        return self.request.user.bookmark_files.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ClusterAPI(RULViewSet):
    serializer_class = serializers.ClusterSerializer

    filterset_class = filters.ClusterFilter
    search_fields = ['@name']
    ordering_fields = ['correlation', 'id']
    ordering = ['-bookmarks_count', '-correlation']

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
        tags_qs = self.request.user.tags.all().annotate(bookmarks_count=Count('bookmarks')).filter(bookmarks_count__gt=2).order_by('-weight')
        tags_prefetch = Prefetch('tags', queryset=tags_qs)
        return qs.prefetch_related('bookmarks', tags_prefetch)

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return models.Cluster.objects.none()

        qs = self.request.user.clusters.all()

        if self.action == 'update' or self.action == 'partial_update':
            pass
        elif self.action == 'list':
            qs = self._prefetch(qs)
        elif self.action == 'retrieve':
            qs = self._prefetch(qs)

        return qs


class ClusterFullListAPI(ClusterAPI):
    serializer_class = serializers.ClusterSerializer.ClusterFullDetails
    pagination_class = None
    ordering = None

    def get_serializer_class(self):
        return self.serializer_class

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.order_by('-bookmarks_count')


class BookmarkAPI(RULViewSet):
    serializer_class = serializers.BookmarkSerializer

    filterset_class = filters.BookmarkFilter
    search_fields = ['words_weights__word', 'title', 'url']
    ordering_fields = ['parent_file_id', 'id']
    ordering = ['id']

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
            limit = minmax(limit, 10, 50)
            qs = qs.order_by('-weight')[:limit]
        elif self.action == 'retrieve':
            qs = qs.prefetch_related('bookmarks')

        return qs


class TagListAPI(ListAPIView):
    serializer_class = serializers.TagSerializer.TagList

    filterset_class = filters.TagFilter
    search_fields = ['@name', '@alias_name']
    ordering_fields = ['weight', 'id']
    ordering = ['-weight']

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return models.Tag.objects.none()
        return self.request.user.tags.all()


class BookmarkShortAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request, uuid):
        bookmark = get_object_or_404(models.Bookmark.objects.all(), uuid=uuid)
        models.BookmarkHistory.objects.create(bookmark=bookmark)
        return HttpResponseRedirect(bookmark.url)
