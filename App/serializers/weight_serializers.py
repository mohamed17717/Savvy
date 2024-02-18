import urllib3
from typing import Dict
from rest_framework import serializers

from App import models, controllers


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
        cleaned = self.__clean_url(obj.url)
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

