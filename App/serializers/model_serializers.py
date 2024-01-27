from rest_framework import serializers
from App import models


class BookmarkFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BookmarkFile
        exclude = ['file_hash']
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


class DocumentWordWeightSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DocumentWordWeight
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

    class Details(serializers.ModelSerializer):
        bookmarks = serializers.SerializerMethodField()

        def get_bookmarks(self, obj):
            return BookmarkSerializer.Details(obj.bookmarks.all(), many=True).data

        class Meta:
            model = models.Tag
            fields = '__all__'

    class Update(serializers.ModelSerializer):
        class Meta:
            model = models.Tag
            fields = ['alias_name']
            extra_kwargs = {
                'alias_name': {'allow_null': True}
            }

    class List(serializers.ModelSerializer):
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

    class Details(serializers.ModelSerializer):
        # tags = TagSerializer(read_only=True, many=True)
        # bookmarks = BookmarkDetailsSerializer(read_only=True, many=True)
        tags = serializers.SerializerMethodField()
        bookmarks = serializers.SerializerMethodField()
        url = serializers.CharField(source='get_absolute_url', read_only=True)

        def get_tags(self, obj):
            total_tags = dict()
            # all tags in one dict
            for bm in obj.bookmarks.all():
                for tag in bm.words_weights.all():
                    total_tags.setdefault(tag.word, 0)
                    total_tags[tag.word] += tag.weight
            # total_tags to list

            def to_list_item(i):
                return {'name': i[0], 'weight': i[1]}

            total_tags = map(to_list_item, total_tags.items())
            total_tags = list(total_tags)
            # sort by weight
            total_tags.sort(key=lambda x: x['weight'], reverse=True)

            return total_tags

        def get_bookmarks(self, obj):
            return BookmarkSerializer.Details(obj.bookmarks.all(), many=True).data

        class Meta:
            model = models.Cluster
            fields = '__all__'

    class Update(serializers.ModelSerializer):
        class Meta:
            model = models.Cluster
            fields = ['name']


class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Bookmark
        fields = '__all__'

    class Details(serializers.ModelSerializer):
        # parent_file = BookmarkFileSerializer(read_only=True)

        # scrapes = ScrapyResponseLogSerializer(read_only=True, many=True)
        # words_weights = DocumentWordWeightSerializer(read_only=True, many=True)

        # webpages = BookmarkWebpageDetailsSerializer(read_only=True, many=True)
        # clusters = ClusterWithTagsSerializer(read_only=True, many=True)

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
