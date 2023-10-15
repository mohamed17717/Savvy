from rest_framework.parsers import MultiPartParser, FormParser

from App import serializers, models

from common.utils.drf.viewsets import CRDLViewSet, RLViewSet


class BookmarkFileAPI(CRDLViewSet):
    # TODO files should be for the user only
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = serializers.BookmarkFileSerializer
    queryset = models.BookmarkFile.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ClusterAPI(RLViewSet):
    # TODO cluster should be for the user only
    serializer_class = serializers.DocumentClusterDetailsSerializer
    queryset = models.DocumentCluster.objects.all()


class BookmarkAPI(RLViewSet):
    # TODO qs should be for the user only
    serializer_class = serializers.BookmarkSerializer
    queryset = models.Bookmark.objects.all()

    def retrieve(self, request, *args, **kwargs):
        self.serializer_class = serializers.BookmarkDetailsSerializer
        return super().retrieve(request, *args, **kwargs)
