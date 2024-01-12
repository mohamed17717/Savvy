from django.db.models import Prefetch, Count, QuerySet

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
        qs = (
            self.request.user.clusters.all()
                .annotate(bookmarks_count=Count('bookmarks'))
                .order_by('-bookmarks_count')
        )

        return self._prefetch(qs)


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
