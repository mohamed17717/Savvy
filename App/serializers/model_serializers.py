from rest_framework import serializers
from App import models

from django.core.cache import cache
from django.urls import reverse

from functools import wraps


def cache_serializer(timeout=60*60*24*3):  # 3 days
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Creating a unique key based on the function name and parameters
            key = f'{func.__name__}_{args}_{kwargs}'
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
        fields = '__all__'
        extra_kwargs = {
            'user': {'read_only': True}
        }


class ScrapyResponseLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ScrapyResponseLog
        fields = '__all__'


class WebpageMetaTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WebpageMetaTag
        fields = '__all__'


class WebpageHeaderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WebpageHeader
        fields = '__all__'


class WordWeightSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WordWeight
        fields = '__all__'


class BookmarkWebpageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BookmarkWebpage
        fields = '__all__'

    class Details(serializers.ModelSerializer):
        meta_tags = WebpageMetaTagSerializer(read_only=True, many=True)
        headers = WebpageHeaderSerializer(read_only=True, many=True)

        class Meta:
            model = models.BookmarkWebpage
            fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tag
        fields = '__all__'

    class TagDetails(serializers.ModelSerializer):
        bookmarks = serializers.SerializerMethodField()

        def get_bookmarks(self, obj):
            serializer_class = BookmarkSerializer.BookmarkDetails
            qs = obj.bookmarks.all()[:10]
            return serializer_class(qs, many=True).data

        class Meta:
            model = models.Tag
            fields = '__all__'

    class TagUpdate(serializers.ModelSerializer):
        class Meta:
            model = models.Tag
            fields = ['alias_name']
            extra_kwargs = {
                'alias_name': {'allow_null': True}
            }

    class TagList(serializers.ModelSerializer):
        name = serializers.SerializerMethodField()
        url = serializers.CharField(source='get_absolute_url', read_only=True)

        def get_name(self, obj):
            return obj.alias_name or obj.name

        class Meta:
            model = models.Tag
            fields = ['id', 'name', 'weight', 'url']
            extra_kwargs = {
                'user': {'read_only': True}
            }


class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Bookmark
        fields = '__all__'

    class BookmarkDetails(serializers.ModelSerializer):
        title = serializers.SerializerMethodField()
        url = serializers.SerializerMethodField()
        opened = serializers.SerializerMethodField()

        def get_opened(self, obj):
            return obj.history.exists()

        def get_url(self, obj):
            request = self.context['request']
            path = reverse('app:bookmark-open-url', kwargs={'uuid': obj.uuid})

            return request.build_absolute_uri(path)

        def get_title(self, obj):
            return (
                obj.title
                or (obj.webpage and obj.webpage.title)
                or obj.url
            )

        class Meta:
            model = models.Bookmark
            fields = '__all__'

    class BookmarkUpdate(serializers.ModelSerializer):
        class Meta:
            model = models.Bookmark
            fields = ['favorite', 'hidden']


class GraphNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GraphNode
        fields = '__all__'

    class NodeDetails(serializers.ModelSerializer):
        children_count = serializers.SerializerMethodField()
        bookmarks_count = serializers.SerializerMethodField()
        name = serializers.SerializerMethodField()

        def get_children_count(self, obj):
            return obj.children.count()

        def get_bookmarks_count(self, obj):
            from common.utils.drf.filters import FullTextSearchFilter
            from App import filters, views

            request = self.context['request']

            bookmarks = request.user.bookmarks.all()
            bookmarks = filters.BookmarkFilter(
                request.GET, queryset=bookmarks).qs
            bookmarks = FullTextSearchFilter().filter_queryset(
                request, bookmarks, views.BookmarkAPI, distinct=False)

            return bookmarks.filter(nodes__path__contains=obj.id).distinct().count()

        def get_name(self, obj):
            # if obj.tags.exists():
            #     name = ', '.join(obj.tags.all().values_list('name', flat=True))
            # else:
            #     leafs_tags = models.Tag.objects.filter(
            #         bookmarks__nodes__in=obj.leafs.all()).distinct().order_by('-weight')
            #     name = ', '.join(leafs_tags.values_list(
            #         'name', flat=True)[:5]) + '.....'

            from common.utils.drf.filters import FullTextSearchFilter
            from App import filters, views

            request = self.context['request']

            bookmarks = request.user.bookmarks.all()
            bookmarks = filters.BookmarkFilter(
                request.GET, queryset=bookmarks).qs
            bookmarks = FullTextSearchFilter().filter_queryset(
                request, bookmarks, views.BookmarkAPI, distinct=False)

            bookmarks = bookmarks.filter(
                nodes__path__contains=obj.id).distinct()

            leafs_tags = models.Tag.objects.filter(
                bookmarks__in=bookmarks).distinct().order_by('-weight')
            name = ', '.join(leafs_tags.values_list(
                'name', flat=True)[:5]) + '.....'

            return name

        class Meta:
            model = models.GraphNode
            exclude = [
                'bookmarks', 'tags', 'similarity_matrix',
                'created_at', 'updated_at', 'user', 'parent',
            ]
