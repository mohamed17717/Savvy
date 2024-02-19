from rest_framework import serializers
from App import models


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


class ClusterSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Cluster
        fields = '__all__'

    class ClusterDetails(serializers.ModelSerializer):
        tags = serializers.SerializerMethodField()
        bookmarks = serializers.SerializerMethodField()
        url = serializers.CharField(source='get_absolute_url', read_only=True)

        def get_tags(self, obj):
            tags = []
            for bm in obj.bookmarks.all()[:10]:
                tags.extend(TagSerializer.TagList(
                    bm.tags.all()[:3], many=True).data)

            tags.sort(key=lambda x: x['weight'], reverse=True)
            return tags[:5]

        def get_bookmarks(self, obj):
            serializer_class = BookmarkSerializer.BookmarkDetails
            qs = obj.bookmarks.all()[:10]
            return serializer_class(qs, many=True).data

        class Meta:
            model = models.Cluster
            fields = '__all__'

    class ClusterFullDetails(ClusterDetails):
        def get_tags(self, obj):
            tags = models.Tag.objects.filter(
                bookmarks__in=obj.bookmarks.all()).distinct().order_by('-weight')
            return TagSerializer.TagList(tags, many=True).data

        def get_bookmarks(self, obj):
            serializer_class = BookmarkSerializer.BookmarkDetails
            qs = obj.bookmarks.all()
            return serializer_class(qs, many=True).data

    class ClusterUpdate(serializers.ModelSerializer):
        class Meta:
            model = models.Cluster
            fields = ['name']


class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Bookmark
        fields = '__all__'

    class BookmarkDetails(serializers.ModelSerializer):
        title = serializers.SerializerMethodField()

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
            fields = ['status']
