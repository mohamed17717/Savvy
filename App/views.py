from rest_framework.parsers import MultiPartParser, FormParser

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

    def get_queryset(self):
        return self.request.user.clusters.all().prefetch_related('bookmarks')


class BookmarkAPI(RLViewSet):
    serializer_class = serializers.BookmarkSerializer

    def get_queryset(self):
        return self.request.user.bookmarks.all()

    def retrieve(self, request, *args, **kwargs):
        self.serializer_class = serializers.BookmarkDetailsSerializer
        return super().retrieve(request, *args, **kwargs)
