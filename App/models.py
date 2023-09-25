import urllib3

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

from common.utils.model_utils import validate_file_size, validate_file_extension
from common.utils.file_utils import load_file

from App.controllers import (
    BookmarkFileManager, BookmarkHTMLFileManager, BookmarkJSONFileManager
)

User = get_user_model()


class BookmarkFile(models.Model):
    """Model to store the uploaded bookmarks-files to make operations on them
    ON_CREATE
        - call the link_collector controller to extract links
        - each link stores in Bookmark model
    ACTIONS
        - only owner can make CRUD operations
    """

    # Relations
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='bookmark_files'
    )

    # Required
    location = models.FileField(
        upload_to='users/bookmarks/',
        validators=[
            validate_file_extension('.html', '.json'),
            validate_file_size(5),
        ]
    )

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Computed
    @property
    def path(self) -> str:
        return self.location.path

    @property
    def file_content(self) -> str:
        return load_file(self.path)

    @property
    def is_html(self) -> bool:
        return self.path.endswith('.html')

    @property
    def is_json(self) -> bool:
        return self.path.endswith('.json')

    @property
    def file_manager(self) -> BookmarkFileManager:
        manager = None
        if self.is_html:
            manager = BookmarkHTMLFileManager
        elif self.is_json:
            manager = BookmarkJSONFileManager

        if manager is None:
            raise ValidationError('Can\'t get the file manager')

        return manager

    @property
    def file_obj(self) -> BookmarkFileManager:
        obj = self.file_manager(self.location)
        return obj

    @property
    def bookmarks(self):
        file_obj = self.file_obj
        file_obj.validate(raise_exception=True)
        return file_obj.get_links()


class Bookmark(models.Model):
    """Main bookmark that got clustered and the whole next flow depend on it
    ON_CREATE
        - call the scraper controller to scrape and get webpages / log response
    ACTIONS
        - CUD operations happened internally -- just (R)ead
    """
    # Relations
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='bookmarks'
    )
    parent_file = models.ForeignKey(
        'App.BookmarkFile', on_delete=models.CASCADE,
        related_name='bookmarks', blank=True, null=True
    )

    # Required
    url = models.URLField()

    # Optionals
    title = models.CharField(max_length=512, blank=True, null=True)
    more_data = models.JSONField(blank=True, null=True)

    # Defaults
    crawled = models.BooleanField(default=False)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Computed
    @property
    def domain(self) -> str:
        # domain with subdomains
        url = urllib3.util.parse_url(self.url)
        return url.host

    @property
    def site_name(self) -> str:
        return self.domain.split('.')[-2]

    # shortcuts
    @classmethod
    def instance_by_parent(cls, parent, data):
        return cls(
            user=parent.user,
            parent_file=parent,
            url=data.pop('url'),
            title=data.pop('title', None),
            more_data=data or None
        )


class ScrapyResponseLog(models.Model):
    # Relations
    bookmark = models.ForeignKey(
        'App.Bookmark', on_delete=models.CASCADE,
        related_name='scrapes', blank=True, null=True
    )
    # Required
    url = models.URLField()
    status_code = models.PositiveSmallIntegerField()
    html_file = models.FileField(
        upload_to='scrape/html/',
        validators=[
            validate_file_extension('.html'), validate_file_size(5),
        ]
    )

    # Optional
    error = models.TextField(blank=True, null=True)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class BookmarkWebpage(models.Model):
    # Relations
    bookmark = models.ForeignKey(
        'App.Bookmark', on_delete=models.CASCADE, related_name='webpages'
    )
    # meta_tags, headers

    # Required
    url = models.URLField()
    title = models.CharField(max_length=512)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class WebpageMetaTag(models.Model):
    # Relations
    webpage = models.ForeignKey(
        'App.BookmarkWebpage', on_delete=models.CASCADE, related_name='meta_tags'
    )

    # Required
    name = models.CharField(max_length=64, default='undefined')
    content = models.TextField(blank=True, null=True)

    # Optional
    attrs = models.JSONField(blank=True, null=True)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class WebpageHeader(models.Model):
    webpage = models.ForeignKey(
        'App.BookmarkWebpage', on_delete=models.CASCADE, related_name='headers'
    )

    # Required
    text = models.TextField()
    level = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(6)]
    )

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def tagname(self) -> str:
        return f'h{self.level}'


class DocumentWordWeight(models.Model):
    # Relations
    # TODO in future -> this field become generic relation
    # to relate with (bookmark / youtube / linkedin / etc...)
    document = models.ForeignKey(
        'App.Bookmark', on_delete=models.CASCADE, related_name='words_weights')

    # Required
    word = models.CharField(max_length=64)
    weight = models.PositiveSmallIntegerField()

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class DocumentCluster(models.Model):
    # Relations
    bookmarks = models.ManyToManyField('App.Bookmark', related_name='clusters')

    # Required
    name = models.CharField(max_length=128)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ClusterTag(models.Model):
    # Relations
    cluster = models.ForeignKey(
        'App.DocumentCluster', on_delete=models.CASCADE, related_name='tags'
    )
    # Required
    name = models.CharField(max_length=64)

    # Defaults
    show = models.BooleanField(default=True)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
