from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT

from App import serializers, models

from Users.serializers import UserSerializer

from common.utils.drf.viewsets import CRUDLViewSet, CRDLViewSet


class BookmarkFileUploadAPI(CRDLViewSet):
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = serializers.BookmarkFileSerializer
    queryset = models.BookmarkFile.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
