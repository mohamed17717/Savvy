import re
from typing import Dict

import urllib3
from rest_framework import serializers

from App import controllers, models


class BookmarkWeightingSerializer(serializers.ModelSerializer):
    """This serializer is used for access, clean and weight bookmark data
    return a vectors of weights for each type
    """

    url = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    domain = serializers.SerializerMethodField()
    site_name = serializers.SerializerMethodField()
    webpage_headers = serializers.SerializerMethodField()
    webpage_meta_data = serializers.SerializerMethodField()

    def get_weight(self, text, weight_factor) -> Dict[str, int]:
        weights: Dict[str, int] = {}
        for word in text.split(" "):
            weights.setdefault(word, 0)
            weights[word] += weight_factor

        # remove empty keys
        weights.pop("", None)
        return weights

    def merge_weights(self, weight1, weight2) -> Dict[str, int]:
        merged = weight1.copy()
        for word, weight in weight2.items():
            merged.setdefault(word, 0)
            merged[word] += weight
        return merged

    def clean_text(self, text) -> str:
        return (
            controllers.TextCleaner(text)
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
            .stemming(method="lem")
            .double_spaces()
        ).text

    def clean_url(self, url) -> str:
        path = urllib3.util.parse_url(url).path
        return (
            controllers.TextCleaner(path)
            .not_letters()
            .underscore()
            .numbers()
            .uncamelcase()
            .stop_words()
            .shorter_than(length=2)
            .double_spaces()
            .lowercase()
        ).text

    def get_url(self, obj) -> Dict[str, int]:
        WEIGHT_FACTOR = 6
        cleaned = self.clean_url(obj.url)
        return self.get_weight(cleaned, WEIGHT_FACTOR)

    def get_title(self, obj) -> Dict[str, int]:
        WEIGHT_FACTOR = 10

        # TODO if titles are not the same do something
        wp = obj.webpage
        wp_title = wp and wp.title
        title = obj.title or wp_title

        if title is None:
            return {}

        cleaned = self.clean_text(title)
        return self.get_weight(cleaned, WEIGHT_FACTOR)

    def get_domain(self, obj) -> Dict[str, int]:
        WEIGHT_FACTOR = 3
        domain = obj.domain
        return self.get_weight(domain, WEIGHT_FACTOR)

    def get_site_name(self, obj) -> Dict[str, int]:
        WEIGHT_FACTOR = 3
        site_name = obj.site_name
        return self.get_weight(site_name, WEIGHT_FACTOR)

    def get_webpage_headers(self, obj) -> Dict[str, int]:
        WEIGHT_FACTOR = 1

        wp = obj.webpage
        if wp is None:
            return {}

        headers = wp.headers.all()
        weights = {}
        for header in headers:
            cleaned = self.clean_text(header.text)
            weight_factor = header.weight_factor * WEIGHT_FACTOR
            header_weight = self.get_weight(cleaned, weight_factor)

            weights = self.merge_weights(weights, header_weight)

        return weights

    def get_webpage_meta_data(self, obj) -> Dict[str, int]:
        WEIGHT_FACTOR = 1

        wp = obj.webpage
        if wp is None:
            return {}

        meta_tags = wp.meta_tags.all()
        weights = {}
        for meta in meta_tags:
            if meta.content is None or meta.name.endswith("id"):
                continue

            cleaned = self.clean_text(meta.content)
            weight_factor = meta.weight_factor * WEIGHT_FACTOR
            meta_weight = self.get_weight(cleaned, weight_factor)

            weights = self.merge_weights(weights, meta_weight)

        return weights

    @property
    def total_weight(self):
        assert self.instance, "You need to set an instance"

        total = {}
        for weight in self.data.values():
            total = self.merge_weights(total, weight)
        return total

    class Meta:
        model = models.Bookmark
        fields = [
            "url",
            "title",
            "domain",
            "site_name",
            "webpage_headers",
            "webpage_meta_data",
        ]


class YoutubeBookmarkWeightingSerializer(BookmarkWeightingSerializer):
    def identify_youtube_link(self, url):
        patterns = (
            ("video", r"youtu\.be\/[\w\-\+]+|youtube\.com\/watch\?v=[\w\-\+]+"),
            ("channel", r"youtube\.com\/channel\/[\w\-\+]+"),
            ("channel", r"youtube\.com\/c\/[\w\-\+]+"),
            ("channel", r"youtube\.com\/[\@\w\-\+]+/[\w\-\+]+"),
            ("user_channel", r"youtube\.com\/user\/[\w\-\+]+"),
            ("playlist", r"youtube\.com\/playlist\?list=[\w\-\+]+"),
            ("shorts", r"youtube\.com\/shorts\/[\w\-\+]+"),
            ("search", r"youtube\.com\/results\?search_query=[\w\-\+]+"),
        )

        return next(
            (
                content_type
                for content_type, pattern in patterns
                if re.search(pattern, url)
            ),
            None,
        )

    def get_url(self, obj) -> Dict[str, int]:
        WEIGHT_FACTOR = 20
        cleaned = self.clean_url(obj.url)
        weight = self.get_weight(cleaned, WEIGHT_FACTOR)

        content_type = self.identify_youtube_link(obj.url)
        if content_type is not None:
            weight[f"yt_{content_type}"] = WEIGHT_FACTOR * 2

        return weight

    def get_title(self, obj) -> Dict[str, int]:
        WEIGHT_FACTOR = 15

        title = obj.title
        if not title:
            return {}

        cleaned = self.clean_text(title)
        return self.get_weight(cleaned, WEIGHT_FACTOR)


class FacebookBookmarkWeightingSerializer(BookmarkWeightingSerializer):
    def identify_facebook_link(self, url):
        patterns = (
            ("page", r"facebook\.com/pg/[\w\.]+/about/?"),
            ("group_member", r"facebook\.com/groups/[\w\.]+/members/?"),
            ("group_post", r"facebook\.com/groups/[\w\.]+/posts/[\w\.]+/?"),
            ("group_user", r"facebook\.com/groups/[\w\.]+/user/[\w\.]+/?"),
            ("group", r"facebook\.com/groups/[\w\.]+/?"),
            ("post", r"facebook\.com/[\w\.]+/posts/[\w\.]+/?"),
            ("post", r"facebook\.com/story\.php/?\?id=[\w\.]+/?"),
            ("post", r"facebook\.com/story\.php/?\?story_fbid=[\w\.]+/?"),
            ("video", r"facebook\.com/[\w\.]+/videos/[\w\.]+/?"),
            ("reels", r"facebook\.com/reel/[\w\.]+/?"),
            ("story", r"facebook\.com/[\w\.]+/stories/[\w\.]+/?"),
            ("watch", r"facebook\.com/watch/[\w\.]+/?"),
            ("live_video", r"facebook\.com/[\w\.]+/live/?[\w\.]+?/?"),
            ("event", r"facebook\.com/events/[\w\.]+/?"),
            ("marketplace_listing", r"facebook\.com/marketplace/item/[\w\.]+/?"),
            ("photo", r"facebook\.com/photo\.php/?\?photo_id=[\w\.]+"),
            ("album", r"facebook\.com/[\w\.]+/photos/[\w\.]+/?"),
            ("fundraiser", r"facebook\.com/fundraisers/[\w\.]+/?"),
            ("search", r"facebook\.com/search_results/?\?q=.+?/?"),
            ("search", r"facebook\.com/search/\w+/?\?q=.+?/?"),
            ("questions", r"facebook\.com/questions\.php/?\?question_id=[\w\.]+/?"),
            ("profile", r"facebook\.com/profile\.php/?\?id=[\w\.]+/?"),
            ("profile", r"facebook\.com/people/.+/?"),
            ("profile", r"facebook\.com/[\w\.]+/?"),
        )

        return next(
            (
                content_type
                for content_type, pattern in patterns
                if re.search(pattern, url)
            ),
            None,
        )

    def get_url(self, obj) -> Dict[str, int]:
        WEIGHT_FACTOR = 20
        cleaned = self.clean_url(obj.url)
        weight = self.get_weight(cleaned, WEIGHT_FACTOR)

        content_type = self.identify_facebook_link(obj.url)
        if content_type is not None:
            weight[f"fb_{content_type}"] = WEIGHT_FACTOR * 2

        return weight

    def get_title(self, obj) -> Dict[str, int]:
        WEIGHT_FACTOR = 15

        title = obj.title
        if not title:
            return {}

        cleaned = self.clean_text(title)
        return self.get_weight(cleaned, WEIGHT_FACTOR)


class InstagramBookmarkWeightingSerializer(BookmarkWeightingSerializer):
    def identify_instagram_link(self, url):
        patterns = (
            ("post", r"instagram\.com/p/([\.\w\-]+)/?"),
            ("reels", r"instagram\.com/reel/([\.\w\-]+)/?"),
            ("story", r"instagram\.com/stories/([\w\.]+)/([\d]+)/?"),
            (
                "igtv",
                r"instagram\.com/tv/([\.\w\-]+)/?$",
            ),
            ("hashtag", r"instagram\.com/explore/tags/([\.\w\-]+)/?"),
            ("search", r"instagram\.com/explore/search/keyword/?"),
            ("profile", r"instagram\.com/([\w\.]+)/?"),
        )

        return next(
            (
                content_type
                for content_type, pattern in patterns
                if re.search(pattern, url)
            ),
            None,
        )

    def get_url(self, obj) -> Dict[str, int]:
        # Url is not important for instagram just care about the pattern
        WEIGHT_FACTOR = 6
        cleaned = self.clean_url(obj.url)
        weight = self.get_weight(cleaned, WEIGHT_FACTOR)

        content_type = self.identify_instagram_link(obj.url)
        if content_type is not None:
            weight[f"ig_{content_type}"] = 20 * 2

        return weight

    def get_title(self, obj) -> Dict[str, int]:
        WEIGHT_FACTOR = 15

        title = obj.title
        if not title:
            return {}

        cleaned = self.clean_text(title)
        return self.get_weight(cleaned, WEIGHT_FACTOR)
