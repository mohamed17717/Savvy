import re


class YoutubeBookmarkWeightingSerializer:
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


class FacebookBookmarkWeightingSerializer:
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


class InstagramBookmarkWeightingSerializer:
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
