import math

from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url

from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response

from App import serializers, filters, models

from common.utils.drf.viewsets import CRDLViewSet, RULViewSet
from common.utils.math_utils import minmax
from realtime.common.jwt_utils import JwtManager

from django.core.cache import cache


def cache_per_user(timeout):
    def decorator(view_func):
        def _wrapped_view(self, request, *args, **kwargs):
            cache_key = f"{request.user.id}-{request.path}"
            response = cache.get(cache_key)
            if not response:
                response = view_func(self, request, *args, **kwargs)
                cache.set(cache_key, response.data, timeout)
            else:
                response = Response(response)
            return response
        return _wrapped_view
    return decorator


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
        # delete cached graph tree
        cache_key = f"{self.request.user.id}-{resolve_url('app:node_graph')}"
        cache.delete(cache_key)


class BookmarkAPI(RULViewSet):
    serializer_class = serializers.BookmarkSerializer

    filterset_class = filters.BookmarkFilter
    search_fields = ['words_weights__word', 'title', 'url']
    ordering_fields = ['parent_file_id', 'id']
    ordering = ['nodes__id', 'id']

    def get_serializer_class(self):
        serializer_class = self.serializer_class

        if self.action == 'update' or self.action == 'partial_update':
            serializer_class = serializers.BookmarkSerializer.BookmarkUpdate
        elif self.action == 'list':
            serializer_class = serializers.BookmarkSerializer.BookmarkDetails
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


class WordGraphNodeAPI(APIView):
    serializer_class = serializers.GraphNodeSerializer.NodeDetails

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return models.GraphNode.objects.none()

        return self.request.user.nodes.all().prefetch_related('children')

    def get(self, request, parent=None):
        qs = self.get_queryset()

        if parent is None:
            qs = qs.filter(parent__isnull=True)
        else:
            qs = qs.filter(parent_id=parent)

        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


class BookmarkFilterChoices:
    class Base(APIView):
        def get_filtered_bookmarks(self, request):
            from common.utils.drf.filters import FullTextSearchFilter

            bookmarks = request.user.bookmarks.all()
            bookmarks = filters.BookmarkFilter(
                request.GET, queryset=bookmarks).qs
            bookmarks = FullTextSearchFilter().filter_queryset(
                request, bookmarks, BookmarkAPI, distinct=False)

            return bookmarks

        def get_choices(self, request, group_by):
            bookmarks = self.get_filtered_bookmarks(request)
            data = bookmarks.values(
                *group_by).annotate(bookmarks_count=Count('id', distinct=True)).order_by('-bookmarks_count')
            return data

        def get(self, request):
            data = self.get_choices(request, self.group_by)
            return Response(data)

    class Website(Base):
        group_by = ['website_id', 'website__domain', 'website__favicon']

    class Topic(Base):
        group_by = ['tags__id', 'tags__name']
