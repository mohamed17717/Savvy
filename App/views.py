import math

from django.db.models import Prefetch, QuerySet

from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.generics import ListAPIView

from App import serializers, filters

from common.utils.drf.viewsets import CRDLViewSet, RLViewSet, RULViewSet
from common.utils.math_utils import dynamic_number_boundaries


class BookmarkFileAPI(CRDLViewSet):
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = serializers.BookmarkFileSerializer

    def get_queryset(self):
        return self.request.user.bookmark_files.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ClusterAPI(RULViewSet):
    # TODO remove this line and leave the pagination
    pagination_class = None
    filterset_class = filters.ClusterFilter

    def get_serializer_class(self):
        serializer_class = serializers.ClusterSerializer

        if self.action == 'update':
            serializer_class = serializers.ClusterSerializer.Update
        elif self.action == 'list':
            serializer_class = serializers.ClusterSerializer.Details
        elif self.action == 'retrieve':
            serializer_class = serializers.ClusterSerializer.Details

        return serializer_class

    def _prefetch(self, qs: QuerySet) -> QuerySet:
        from App.models import DocumentWordWeight as WordWeight

        user = self.request.user
        words_query_kwargs = {'important': True, 'bookmark__user': user}
        words_qs = (
            WordWeight.objects.filter(**words_query_kwargs).order_by('-weight')
        )
        words_prefetch = Prefetch(
            'bookmarks__words_weights', queryset=words_qs)

        return qs.prefetch_related('bookmarks', words_prefetch)

    def get_queryset(self):
        qs = self.request.user.clusters.all()

        if self.action == 'update':
            pass
        elif self.action == 'list':
            qs = qs.order_by('-correlation')
            qs = self._prefetch(qs)
        elif self.action == 'retrieve':
            qs = self._prefetch(qs)

        return qs


class BookmarkAPI(RULViewSet):
    filterset_class = filters.BookmarkFilter

    def get_serializer_class(self):
        serializer_class = serializers.BookmarkSerializer

        if self.action == 'update':
            serializer_class = serializers.BookmarkSerializer.Update
        elif self.action == 'list':
            pass
        elif self.action == 'retrieve':
            serializer_class = serializers.BookmarkSerializer.Details

        return serializer_class

    def get_queryset(self):
        qs = self.request.user.bookmarks.all()

        if self.action == 'update':
            pass
        elif self.action == 'list':
            pass
        elif self.action == 'retrieve':
            pass

        return qs


class TagAPI(RULViewSet):
    pagination_class = None

    def get_serializer_class(self):
        serializer_class = serializers.TagSerializer

        if self.action == 'update':
            serializer_class = serializers.TagSerializer.Update
        elif self.action == 'list':
            serializer_class = serializers.TagSerializer.List
        elif self.action == 'retrieve':
            # TODO paginate RCs in the Tag
            serializer_class = serializers.TagSerializer.Details

        return serializer_class

    def get_queryset(self):
        qs = self.request.user.tags.all()

        if self.action == 'update':
            pass
        elif self.action == 'list':
            limit = math.ceil(qs.count() * 0.1)
            limit = dynamic_number_boundaries(limit, 10, 50)
            qs = qs.order_by('-weight')[:limit]
        elif self.action == 'retrieve':
            qs = qs.prefetch_related('bookmarks')

        return qs


class TagListAPI(ListAPIView):
    serializer_class = serializers.TagSerializer.List
    filterset_class = filters.TagFilter

    def get_queryset(self):
        return self.request.user.tags.all().order_by('-weight')
