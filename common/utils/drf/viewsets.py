from rest_framework import viewsets, mixins, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response


class UDViewSet(mixins.UpdateModelMixin,
                mixins.DestroyModelMixin,
                viewsets.GenericViewSet):
    pass


class RUDViewSet(mixins.UpdateModelMixin,
                 mixins.RetrieveModelMixin,
                 mixins.DestroyModelMixin,
                 viewsets.GenericViewSet):
    pass


class CRUDViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):
    """All without LIST"""
    pass


class CUDViewSet(mixins.CreateModelMixin,
                 mixins.UpdateModelMixin,
                 mixins.DestroyModelMixin,
                 viewsets.GenericViewSet):
    """All without LIST, RETRIEVE"""
    pass


class CRUDLViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    pass


class CRLViewSet(mixins.CreateModelMixin,
                 mixins.RetrieveModelMixin,
                 mixins.ListModelMixin,
                 viewsets.GenericViewSet):
    pass


class RLViewSet(mixins.RetrieveModelMixin,
                mixins.ListModelMixin,
                viewsets.GenericViewSet):
    pass


class BulkModelViewSet(CRUDLViewSet):
    """Allow to do operations for the model in bulk
    - create // delete accept many
    """
    @action(detail=False, methods=['POST'])
    def create_bulk(self, request):
        # Deserialize the data and create instances in bulk
        serializer = self.serializer_class(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def __validate_data(self, data):
        class RequestSerializer(serializers.Serializer):
            ids = serializers.ListField(
                child=serializers.IntegerField(), required=True
            )

        RequestSerializer(data=data).is_valid(raise_exception=True)

    @action(detail=False, methods=['DELETE'])
    def delete_bulk(self, request):
        self.__validate_data(request.data)
        self.queryset.filter(id__in=request.data['ids']).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['PUT', 'PATCH'], )
    def update_bulk(self, request):
        self.__validate_data(request.data)

        data = request.data
        ids = data.pop('ids')
        qs = self.queryset.filter(id__in=ids)
        qs.update(**data)

        serializer = self.serializer_class(qs, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
