import math
from datetime import timedelta

from django.core.cache import cache
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from App import filters, models, serializers
from common.utils.drf.filters import FullTextSearchFilter
from common.utils.drf.serializers import only_fields
from common.utils.drf.viewsets import CRDLViewSet, RUDLViewSet, RULViewSet
from common.utils.math_utils import minmax
from realtime.common.jwt_utils import JwtManager


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
        JwtManager.inject_cookie(response, data={"user_id": request.user.id})

        return response

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return models.BookmarkFile.objects.none()

        return self.request.user.bookmark_files.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BookmarkAPI(RUDLViewSet):
    serializer_class = serializers.BookmarkSerializer

    filterset_class = filters.BookmarkFilter
    search_fields = ["words_weights__word", "title", "url"]
    ordering_fields = ["id", "parent_file_id"]

    @property
    def ordering(self):
        if self.action == "history_list":
            return ["-history__created_at"]
        return ["nodes__id", "added_at"]  # 'id',

    def get_serializer_class(self):
        serializer_class = self.serializer_class

        list_actions = [
            "list",
            "archived_list",
            "deleted_list",
            "favorite_list",
            "retrieve",
            "history_list",
        ]

        if self.action in ["update", "partial_update"]:
            serializer_class = serializers.BookmarkSerializer.BookmarkUpdate
        elif self.action in list_actions:
            serializer_class = serializers.BookmarkSerializer.BookmarkDetails

        return serializer_class

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return models.Bookmark.objects.none()

        qs = self.request.user.bookmarks.all()

        archive_actions = ["permanent_delete", "restore", "archived_destroy"]
        all_actions = ["open_url"]

        if self.action == "archived_list":
            qs = models.Bookmark.hidden_objects.all().by_user(self.request.user)
            qs = qs.filter(delete_scheduled_at__isnull=True)
        elif self.action == "deleted_list":
            qs = models.Bookmark.hidden_objects.all().by_user(self.request.user)
            qs = qs.filter(delete_scheduled_at__isnull=False)
        elif self.action == "favorite_list":
            qs = self.request.user.bookmarks.all()
            qs = qs.filter(favorite=True)
        elif self.action == "history_list":
            qs = self.request.user.bookmarks.all()
            qs = qs.filter(history__isnull=False)

        elif self.action in archive_actions:
            qs = models.Bookmark.hidden_objects.all().by_user(self.request.user)
        elif self.action in all_actions:
            qs = models.Bookmark.all_objects.all().by_user(self.request.user)

        if self.action.endswith("list"):
            return (
                qs.only(*only_fields(self.get_serializer_class()))
                .select_related("website")
                .prefetch_related("history")
            )
        return qs

    def perform_destroy(self, instance):
        instance.hidden = True
        instance.delete_scheduled_at = timezone.now() + timedelta(days=14)
        instance.save(update_fields=["hidden", "delete_scheduled_at"])

    def perform_restore(self, instance):
        instance.hidden = False
        instance.delete_scheduled_at = None
        instance.save(update_fields=["hidden", "delete_scheduled_at"])

    @action(
        methods=["delete"], detail=False, url_path=r"(?P<pk>[\d]+)/permanent-delete"
    )
    def permanent_delete(self, request, pk):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=["get"], detail=False, url_path=r"(?P<pk>[\d]+)/restore")
    def restore(self, request, pk):
        instance = self.get_object()
        self.perform_restore(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=["delete"], detail=False, url_path=r"(?P<pk>[\d]+)/archived-delete")
    def archived_destroy(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["get"],
        detail=False,
        url_path=r"(?P<uuid>[\w-]+)/open",
        permission_classes=[AllowAny],
    )
    def open_url(self, request, uuid):
        bookmark = get_object_or_404(models.Bookmark.objects.all(), uuid=uuid)
        models.BookmarkHistory.objects.create(bookmark=bookmark)
        return HttpResponseRedirect(bookmark.url)

    @action(methods=["get"], detail=False, url_path="archived-list")
    def archived_list(self, request):
        return super().list(request)

    @action(methods=["get"], detail=False, url_path="deleted-list")
    def deleted_list(self, request):
        return super().list(request)

    @action(methods=["get"], detail=False, url_path="favorite-list")
    def favorite_list(self, request):
        return super().list(request)

    @action(methods=["get"], detail=False, url_path="history-list")
    def history_list(self, request):
        return super().list(request)


class TagAPI(RULViewSet):
    pagination_class = None
    serializer_class = serializers.TagSerializer

    def get_serializer_class(self):
        serializer_class = self.serializer_class

        if self.action in ["update", "partial_update"]:
            serializer_class = serializers.TagSerializer.TagUpdate
        elif self.action == "list":
            serializer_class = serializers.TagSerializer.TagList
        elif self.action == "retrieve":
            serializer_class = serializers.TagSerializer.TagDetails

        return serializer_class

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return models.Tag.objects.none()

        # Using this function from the manager
        # to filtering tags with small amount of bookmarks
        qs = models.Tag.objects.all().by_user(self.request.user)

        if self.action == "list":
            limit = math.ceil(qs.count() * 0.1)
            limit = minmax(limit, 10, 50)
            qs = qs.order_by("-weight")[:limit]
        elif self.action == "retrieve":
            qs = qs.prefetch_related("bookmarks")

        return qs


class TagListAPI(ListAPIView):
    serializer_class = serializers.TagSerializer.TagList

    filterset_class = filters.TagFilter
    search_fields = ["@name", "@alias_name"]
    ordering_fields = ["weight", "id"]
    ordering = ["-weight"]

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return models.Tag.objects.none()
        return models.Tag.objects.all().by_user(self.request.user)


class BookmarkFilterChoices:
    class Base(ListAPIView):
        def get_bookmarks(self):
            bookmarks = self.request.user.bookmarks.all()
            bookmarks = filters.BookmarkFilter(self.request.GET, queryset=bookmarks).qs
            bookmarks = FullTextSearchFilter().filter_queryset(
                self.request, bookmarks, BookmarkAPI, distinct=False
            )

            return bookmarks

        def get_queryset(self):
            if self.request.user.is_anonymous:
                return self.model.objects.none()

            bookmarks = self.get_bookmarks()
            qs = (
                self.get_related_qs()
                .filter(bookmarks__in=bookmarks)
                .annotate(num_bookmarks=Count("bookmarks", distinct=True))
                .filter(num_bookmarks__gt=0)
            )

            if search_query := self.request.GET.get(self.search_param):
                lookup = {f"{self.search_field}__icontains": search_query}
                qs = qs.filter(**lookup)

            return qs

    class Website(Base):
        serializer_class = serializers.WebsiteSerializer.WebsiteFilterChoicesList
        model = models.Website
        search_param = "website_search"
        search_field = "domain"

        def get_related_qs(self):
            return self.request.user.websites.all()

    class Topic(Base):
        serializer_class = serializers.TagSerializer.TagFilterChoicesList
        ordering = ["-weight"]
        model = models.Tag
        search_param = "tags_search"
        search_field = "name"

        def get_related_qs(self):
            return models.Tag.objects.all().by_user(self.request.user)
