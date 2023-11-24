from rest_framework import serializers

from App import models


class BookmarkFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BookmarkFile
        fields = '__all__'
        extra_kwargs = {
            'user': {'read_only': True}
        }


class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Bookmark
        fields = '__all__'


class ScrapyResponseLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ScrapyResponseLog
        fields = '__all__'


class BookmarkWebpageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BookmarkWebpage
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


class DocumentClusterSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DocumentCluster
        fields = '__all__'


class ClusterTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ClusterTag
        fields = '__all__'


# Details Serializers

class DocumentClusterWithTagsSerializer(serializers.ModelSerializer):
    tags = ClusterTagSerializer(read_only=True, many=True)

    class Meta:
        model = models.DocumentCluster
        fields = '__all__'


class BookmarkWebpageDetailsSerializer(serializers.ModelSerializer):
    meta_tags = WebpageMetaTagSerializer(read_only=True, many=True)
    headers = WebpageHeaderSerializer(read_only=True, many=True)

    class Meta:
        model = models.BookmarkWebpage
        fields = '__all__'


class BookmarkDetailsSerializer(serializers.ModelSerializer):
    parent_file = BookmarkFileSerializer(read_only=True)

    scrapes = ScrapyResponseLogSerializer(read_only=True, many=True)
    words_weights = DocumentWordWeightSerializer(read_only=True, many=True)

    webpages = BookmarkWebpageDetailsSerializer(read_only=True, many=True)
    clusters = DocumentClusterWithTagsSerializer(read_only=True, many=True)

    title = serializers.SerializerMethodField()

    def get_title(self, obj):
        return (
            obj.title
            or (obj.webpages.last() and obj.webpages.last().title)
            or obj.url
        )

    class Meta:
        model = models.Bookmark
        fields = '__all__'


class DocumentClusterDetailsSerializer(serializers.ModelSerializer):
    tags = ClusterTagSerializer(read_only=True, many=True)
    bookmarks = BookmarkDetailsSerializer(read_only=True, many=True)

    class Meta:
        model = models.DocumentCluster
        fields = '__all__'
