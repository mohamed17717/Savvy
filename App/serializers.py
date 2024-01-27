import urllib3
from typing import Dict
from rest_framework import serializers

from App import models, controllers


class BookmarkFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BookmarkFile
        exclude = ['file_hash']
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


# ------------------------ Details Serializers ------------------------ #

class BookmarkWebpageDetailsSerializer(serializers.ModelSerializer):
    meta_tags = WebpageMetaTagSerializer(read_only=True, many=True)
    headers = WebpageHeaderSerializer(read_only=True, many=True)

    class Meta:
        model = models.BookmarkWebpage
        fields = '__all__'


class BookmarkDetailsSerializer(serializers.ModelSerializer):
    # parent_file = BookmarkFileSerializer(read_only=True)

    # scrapes = ScrapyResponseLogSerializer(read_only=True, many=True)
    # words_weights = DocumentWordWeightSerializer(read_only=True, many=True)

    # webpages = BookmarkWebpageDetailsSerializer(read_only=True, many=True)
    # clusters = DocumentClusterWithTagsSerializer(read_only=True, many=True)

    # title = serializers.SerializerMethodField()

    def get_title(self, obj):
        return (
            obj.title
            or (obj.webpage and obj.webpage.title)
            or obj.url
        )

    class Meta:
        model = models.Bookmark
        fields = '__all__'


class DocumentClusterDetailsSerializer(serializers.ModelSerializer):
    # tags = TagSerializer(read_only=True, many=True)
    # bookmarks = BookmarkDetailsSerializer(read_only=True, many=True)

    tags = serializers.SerializerMethodField()
    bookmarks = serializers.SerializerMethodField()

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
        return BookmarkDetailsSerializer(obj.bookmarks.all(), many=True).data

    class Meta:
        model = models.DocumentCluster
        fields = '__all__'


class BookmarkWeightingSerializer(serializers.ModelSerializer):
    '''This serializer is used for access, clean and weight bookmark data
    return a vectors of weights for each type
    '''
    url = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    domain = serializers.SerializerMethodField()
    site_name = serializers.SerializerMethodField()
    webpage_headers = serializers.SerializerMethodField()
    webpage_meta_data = serializers.SerializerMethodField()

    def __weight(self, text, weight_factor) -> Dict[str, int]:
        weights = {}
        for word in text.split(' '):
            weights.setdefault(word, 0)
            weights[word] += weight_factor

        # remove empty keys
        weights.pop('', None)
        return weights

    def __merge_weights(self, weight1, weight2) -> Dict[str, int]:
        merged = weight1.copy()
        for word, weight in weight2.items():
            merged.setdefault(word, 0)
            merged[word] += weight
        return merged

    def __clean_text(self, text) -> str:
        cleaned = (controllers.TextCleaner(text)
                   .html_entities()
                   .html_tags()
                   .emails()
                   .usernames()
                   .links()
                   .hashtags()
                   .longer_than(length=20)
                   .repeating_chars()
                   .lines()
                   .not_letters()
                   .underscore()
                   .numbers()
                   # .uncamelcase()
                   .lowercase()
                   .stop_words()
                   .shorter_than(length=2)
                   .stemming(method='lem')
                   .double_spaces()
                   ).text
        return cleaned

    def __clean_url(self, url) -> str:
        path = urllib3.util.parse_url(url).path
        cleaned = (controllers.TextCleaner(path)
                   .not_letters()
                   .underscore()
                   .numbers()
                   .uncamelcase()
                   .stop_words()
                   .shorter_than(length=2)
                   .double_spaces()
                   .lowercase()
                   ).text
        return cleaned

    def get_url(self, obj) -> Dict[str, int]:
        WEIGHT_FACTOR = 6

        # TODO if urls are not the same do something
        wp = obj.webpage
        wp_url = wp and wp.url
        url = obj.url or wp_url

        cleaned = self.__clean_url(url)
        return self.__weight(cleaned, WEIGHT_FACTOR)

    def get_title(self, obj) -> Dict[str, int]:
        WEIGHT_FACTOR = 10

        # TODO if titles are not the same do something
        wp = obj.webpage
        wp_title = wp and wp.title
        title = obj.title or wp_title

        if title is None:
            return {}

        cleaned = self.__clean_text(title)
        return self.__weight(cleaned, WEIGHT_FACTOR)

    def get_domain(self, obj) -> Dict[str, int]:
        WEIGHT_FACTOR = 3
        domain = obj.domain
        return self.__weight(domain, WEIGHT_FACTOR)

    def get_site_name(self, obj) -> Dict[str, int]:
        WEIGHT_FACTOR = 3
        site_name = obj.site_name
        return self.__weight(site_name, WEIGHT_FACTOR)

    def get_webpage_headers(self, obj) -> Dict[str, int]:
        WEIGHT_FACTOR = 1

        wp = obj.webpage
        if wp is None:
            return {}

        headers = wp.headers.all()
        weights = {}
        for header in headers:
            cleaned = self.__clean_text(header.text)
            weight_factor = header.weight_factor * WEIGHT_FACTOR
            header_weight = self.__weight(cleaned, weight_factor)

            weights = self.__merge_weights(weights, header_weight)

        return weights

    def get_webpage_meta_data(self, obj) -> Dict[str, int]:
        WEIGHT_FACTOR = 1

        wp = obj.webpage
        if wp is None:
            return {}

        meta_tags = wp.meta_tags.all()
        weights = {}
        for meta in meta_tags:
            if meta.content is None or meta.name.endswith('id'):
                continue

            cleaned = self.__clean_text(meta.content)
            weight_factor = meta.weight_factor * WEIGHT_FACTOR
            meta_weight = self.__weight(cleaned, weight_factor)

            weights = self.__merge_weights(weights, meta_weight)

        return weights

    @property
    def total_weight(self):
        assert self.instance, 'You need to set an instance'

        total = {}
        for weight in self.data.values():
            total = self.__merge_weights(total, weight)
        return total

    class Meta:
        model = models.Bookmark
        fields = [
            'url',
            'title',
            'domain',
            'site_name',
            'webpage_headers',
            'webpage_meta_data',
        ]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tag
        fields = '__all__'

    class Details(serializers.ModelSerializer):
        bookmarks = BookmarkDetailsSerializer(read_only=True, many=True)

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


class DocumentClusterWithTagsSerializer(serializers.ModelSerializer):
    tags = TagSerializer.List(read_only=True, many=True)

    class Meta:
        model = models.DocumentCluster
        fields = '__all__'
