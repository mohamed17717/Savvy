from functools import wraps

from django.core.cache import cache
from django.urls import reverse
from rest_framework import serializers

from App import models


def cache_serializer(timeout=60 * 60 * 24 * 3):  # 3 days
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Creating a unique key based on the function name and parameters
            key = f"{func.__name__}_{args}_{kwargs}"
            if cached_result := cache.get(key):
                return cached_result
            result = func(self, *args, **kwargs)
            cache.set(key, result, timeout)
            return result

        return wrapper

    return decorator


class BookmarkFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BookmarkFile
        fields = "__all__"
        extra_kwargs = {"user": {"read_only": True}}


class ScrapyResponseLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ScrapyResponseLog
        fields = "__all__"


class WebpageMetaTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WebpageMetaTag
        fields = "__all__"


class WebpageHeaderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WebpageHeader
        fields = "__all__"


class BookmarkWebpageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BookmarkWebpage
        fields = "__all__"

    class Details(serializers.ModelSerializer):
        meta_tags = WebpageMetaTagSerializer(read_only=True, many=True)
        headers = WebpageHeaderSerializer(read_only=True, many=True)

        class Meta:
            model = models.BookmarkWebpage
            fields = "__all__"


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tag
        fields = "__all__"

    class TagDetails(serializers.ModelSerializer):
        bookmarks = serializers.SerializerMethodField()

        def get_bookmarks(self, obj):
            serializer_class = BookmarkSerializer.BookmarkDetails
            qs = obj.bookmarks.all()[:10]
            return serializer_class(qs, many=True).data

        class Meta:
            model = models.Tag
            fields = "__all__"

    class TagList(serializers.ModelSerializer):
        name = serializers.SerializerMethodField()
        url = serializers.CharField(source="get_absolute_url", read_only=True)

        def get_name(self, obj):
            return obj.name

        class Meta:
            model = models.Tag
            fields = ["id", "name", "url"]
            extra_kwargs = {"user": {"read_only": True}}

    class TagFilterChoicesList(serializers.ModelSerializer):
        bookmarks_count = serializers.SerializerMethodField()

        def get_bookmarks_count(self, obj):
            return obj.num_bookmarks

        class Meta:
            model = models.Tag
            fields = ["id", "name", "bookmarks_count"]


class WebsiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Website
        fields = "__all__"

    class WebsiteFilterChoicesList(serializers.ModelSerializer):
        bookmarks_count = serializers.SerializerMethodField()

        def get_bookmarks_count(self, obj):
            return obj.num_bookmarks

        class Meta:
            model = models.Website
            fields = ["id", "domain", "favicon", "bookmarks_count"]


class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Bookmark
        exclude = ["search_vector"]

    class BookmarkDetails(serializers.ModelSerializer):
        title = serializers.SerializerMethodField()
        url = serializers.SerializerMethodField()
        opened = serializers.SerializerMethodField()
        domain = serializers.ReadOnlyField(source="website.domain")
        icon = serializers.ReadOnlyField(source="website.favicon")

        def get_opened(self, obj):
            return obj.history.exists()

        def get_url(self, obj):
            request = self.context["request"]
            path = reverse("app:bookmark-open-url", kwargs={"uuid": obj.uuid})

            return request.build_absolute_uri(path)

        def get_title(self, obj):
            return obj.title or (obj.webpage and obj.webpage.title) or obj.url

        class Meta:
            model = models.Bookmark
            exclude = ["search_vector", "more_data", "delete_scheduled_at", "image_url"]

    class BookmarkUpdate(serializers.ModelSerializer):
        class Meta:
            model = models.Bookmark
            fields = ["favorite", "hidden"]
