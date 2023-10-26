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
    queryset = models.DocumentCluster.objects.all().prefetch_related('tags', 'bookmarks')


class BookmarkAPI(RLViewSet):
    # TODO qs should be for the user only
    serializer_class = serializers.BookmarkSerializer

    def get_queryset(self):
        qs = models.Bookmark.objects.all()
        if self.action == 'retrieve':
            related_fields = ['parent_file']
            prefetch_fields = [
                'scrapes', 'webpages', 'clusters', 'words_weights',
                'webpages__meta_tags', 'webpages__headers',
                'clusters__tags'
            ]
            qs = qs.prefetch_related(
                *prefetch_fields).select_related(*related_fields)

        return qs

    def retrieve(self, request, *args, **kwargs):
        self.serializer_class = serializers.BookmarkDetailsSerializer
        return super().retrieve(request, *args, **kwargs)
