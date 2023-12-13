from django.db.models import Prefetch
from django.db.models import Count

from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.generics import UpdateAPIView, GenericAPIView
from rest_framework.response import Response

from App import serializers

from common.utils.drf.viewsets import CRDLViewSet, RLViewSet


class BookmarkFileAPI(CRDLViewSet):
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = serializers.BookmarkFileSerializer

    def get_queryset(self):
        return self.request.user.bookmark_files.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ClusterAPI(RLViewSet):
    serializer_class = serializers.DocumentClusterDetailsSerializer
    # TODO remove this line and leave the pagination
    pagination_class = None

    def get_queryset(self):
        from App.models import Tag, DocumentWordWeight
        tags_prefetch = Prefetch('bookmarks__tags', queryset=Tag.objects.all().order_by('-weight'))
        words_prefetch = Prefetch('bookmarks__words_weights', queryset=DocumentWordWeight.objects.all().order_by('-weight'))
        
        qs = self.request.user.clusters.all()
        qs = qs.annotate(bookmarks_count=Count('bookmarks'))
        qs = qs.order_by('-bookmarks_count')
        qs = qs.prefetch_related('bookmarks', tags_prefetch, words_prefetch)

        return qs


class BookmarkAPI(RLViewSet):
    serializer_class = serializers.BookmarkSerializer

    def get_queryset(self):
        return self.request.user.bookmarks.all()

    def retrieve(self, request, *args, **kwargs):
        self.serializer_class = serializers.BookmarkDetailsSerializer
        return super().retrieve(request, *args, **kwargs)


class TagAPI(RLViewSet):
    serializer_class = serializers.TagDetailsSerializer

    def get_queryset(self):
        return self.request.user.tags.all().prefetch_related('bookmarks')


class TagUpdateAliasNameAPI(UpdateAPIView):
    serializer_class = serializers.TagUpdateAliasNameSerializer

    def get_queryset(self):
        user = self.request.user
        return user.tags.all()


class TagMostWeightedListAPI(GenericAPIView):
    # TODO move this endpoint to TagAPI list method instead
    serializer_class = serializers.TagSerializer
    TAGS_COUNT = 50

    def get_queryset(self):
        user = self.request.user
        return user.tags.all().order_by('-weight')[:self.TAGS_COUNT]

    def get(self, request):
        qs = self.get_queryset()
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)
