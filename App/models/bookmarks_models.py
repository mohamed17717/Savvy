import os
import urllib3
import hashlib
from datetime import date, timedelta

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from django.core.files import File
from django.db.models import QuerySet
from django.utils import timezone

from crawler import settings as scrapy_settings

from common.utils.model_utils import FileSizeValidator
from common.utils.string_utils import random_string

from App.controllers import (
    BookmarkFileManager, BookmarkHTMLFileManager, BookmarkJSONFileManager,
    TextCleaner
)
from App.controllers import document_cluster as doc_cluster


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
            FileExtensionValidator(['html', 'json']), FileSizeValidator(5)
        ]
    )

    # Holder
    tasks = models.JSONField(default=list, blank=True)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.full_clean()  # To make sure field validators run
        return super().save(*args, **kwargs)

    # Computed
    @property
    def path(self) -> str:
        return self.location.path

    @property
    def file_content(self) -> str:
        return self.location.read().decode('utf8')

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
        self.location.seek(0)
        obj = self.file_manager(self.location)
        return obj

    @property
    def bookmarks_links(self):
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

    def __str__(self) -> str:
        return f'{self.id} - {self.url}'

    # Computed
    @property
    def domain(self) -> str:
        # domain with subdomains
        url = urllib3.util.parse_url(self.url)
        return url.host

    @property
    def site_name(self) -> str:
        return self.domain.split('.')[-2]

    @property
    def webpage(self):
        return self.webpages.order_by('-id').first()

    @property
    def summary(self) -> dict:
        """Return the minimum text/phrases you
        will use in weighting and processing
        """
        wp = self.webpage
        result = {
            # TODO get the useful text from the url
            'url': (self.url, 5),
            'title': (self.title, 5),
            'domain': (self.domain, 4),
            'site_name': (self.site_name, 4),
        }
        if wp:
            result.update({
                'webpage': {
                    'url': (wp.url, 5),
                    'title': (wp.title, 5),
                    # NOTE already cleaned
                    'headers': {
                        h.tagname: (h.cleaned_text, 2 * h.weight_factor)
                        for h in wp.headers.all()
                    },
                    # NOTE already cleaned
                    'meta_data': [
                        # (meta.cleaned_content, 3*meta.weight_factor)
                        (meta.content, 3*meta.weight_factor)
                        for meta in wp.meta_tags.all()
                    ]
                }
            })
        return result

    @property
    def summary_flat(self) -> list:
        # TODO skip nulls
        summary = self.summary
        wp = summary.pop('webpage', {})
        headers = wp.pop('headers', {})
        meta = wp.pop('meta_data', [])
        return [
            *summary.values(), *wp.values(), *headers.values(), *meta
        ]

    @property
    def word_vector(self) -> dict:
        vector = {}
        for text, weight in self.summary_flat:
            if text is None:
                continue

            for word in text.split(' '):
                vector.setdefault(word, 0)
                vector[word] += weight

        return vector

    # methods
    def store_word_vector(self):
        from . import DocumentWordWeight
        # Delete the old data , store new ones
        self.words_weights.all().delete()

        words_weights = [
            DocumentWordWeight(
                bookmark=self, word=word, weight=weight
            )
            for word, weight in self.word_vector.items()
        ]

        return DocumentWordWeight.objects.bulk_create(words_weights)

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

    @classmethod
    def cluster_bookmarks(cls, bookmarks: QuerySet['Bookmark']):
        from . import DocumentCluster

        bookmark_id = [b.id for b in bookmarks]
        bookmarks = cls.objects.filter(id__in=bookmark_id)
        vectors = [b.word_vector for b in bookmarks]

        sim_calculator = doc_cluster.CosineSimilarityCalculator(vectors)
        similarity_matrix = sim_calculator.similarity()

        cluster_maker = doc_cluster.ClusterMaker(
            bookmark_id, similarity_matrix, 0.4)
        flat_clusters = cluster_maker.clusters_flat()

        clusters_qs = [bookmarks.filter(id__in=cluster)
                       for cluster in flat_clusters]
        clusters_objects = []
        for cluster in clusters_qs:
            user = cluster[0].user
            cluster_object = DocumentCluster.objects.create(
                user=user, name=random_string(12))
            cluster_object.bookmarks.set(cluster)
            clusters_objects.append(cluster_object)
            # cluster_object.refresh_labels()

        return clusters_objects


class ScrapyResponseLog(models.Model):
    # Relations
    bookmark = models.ForeignKey(
        'App.Bookmark', on_delete=models.CASCADE,
        related_name='scrapes',
        # TODO remove this
        blank=True, null=True
    )
    # Required
    url = models.URLField()
    status_code = models.PositiveSmallIntegerField()

    # Optional
    html_file = models.FileField(
        upload_to='scrape/html/',
        validators=[
            FileExtensionValidator(['html']), FileSizeValidator(5),
        ],
        blank=True, null=True
    )
    error = models.TextField(blank=True, null=True)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    LIFE_LONG = timedelta(days=50)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.id} - [{self.status_code}] {self.url} -> ({self.bookmark.id})'

    def store_file(self, content):
        # Create a unique file name based on the URL hash
        url_hash = hashlib.md5(self.url.encode()).hexdigest()
        file_name = f"{url_hash}.html"
        file_path = os.path.join(scrapy_settings.STORAGE_PATH, file_name)
        i = 0
        while os.path.exists(file_path):
            i += 1
            file_name = f"{url_hash}({i}).html"
            file_path = os.path.join(scrapy_settings.STORAGE_PATH, file_name)

        with open(file_path, 'wb+') as f:
            dj_file = File(f)

            if type(content) is str:
                content = content.encode('utf8')

            dj_file.write(content)
            self.html_file = dj_file
            self.save()

        return file_path

    @classmethod
    def is_url_exists(cls, url, life_long=None):
        if life_long is None:
            life_long = cls.LIFE_LONG
        # if passed 50 days then scrape it again
        # white_date = date.today() - cls.LIFE_LONG
        # return cls.objects.filter(
        #     url=url, error__isnull=True, created_at__date__gte=white_date
        # ).exists()
        
        white_date = timezone.now() - life_long
        return cls.objects.filter(
            url=url, error__isnull=True, created_at__gte=white_date
        ).exists()


class BookmarkWebpage(models.Model):
    # Relations
    bookmark = models.ForeignKey(
        'App.Bookmark', on_delete=models.CASCADE, related_name='webpages',
        # TODO remove this
        blank=True, null=True
    )

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
    # TODO make it 64 when cleaner work fine
    name = models.CharField(max_length=2048, default='undefined')
    content = models.TextField(blank=True, null=True)
    cleaned_content = models.TextField(blank=True, null=True)

    # Optional
    attrs = models.JSONField(blank=True, null=True)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TODO may need this
    # ALLOWED_NAMES = [
    #     'name', 'application-name', 'title', 'site_name', 'description', 'keywords',
    #     'language', 'locale', 'image', 'updated_time', 'site', 'creator', 'url'
    # ]

    def save(self, *args, **kwargs) -> None:
        if self.content:
            self.cleaned_content = TextCleaner(self.content).full_clean().text

        return super().save(*args, **kwargs)

    @property
    def weight_factor(self) -> int:
        # TODO make sure name saved lower case and without and colon prefix or suffix
        factors_map = {
            'keywords': 5
        }
        return factors_map.get(self.name, 1)

    @classmethod
    def bulk_create(cls, webpage: BookmarkWebpage, tags: list[dict]):
        tag_objects = []
        for tag in tags:
            tag_objects.append(cls(
                webpage=webpage, name=tag.get('name', 'UNKNOWN'),
                content=tag.get('content'), attrs=tag
            ))
        return cls.objects.bulk_create(tag_objects)


class WebpageHeader(models.Model):
    webpage = models.ForeignKey(
        'App.BookmarkWebpage', on_delete=models.CASCADE, related_name='headers'
    )

    # Required
    text = models.TextField()
    level = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(6)]
    )
    cleaned_text = models.TextField(blank=True, null=True)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs) -> None:
        cleaner = TextCleaner(self.text)
        cleaner.full_clean()
        self.cleaned_text = cleaner.text

        return super().save(*args, **kwargs)

    @property
    def tagname(self) -> str:
        return f'h{self.level}'

    @property
    def weight_factor(self) -> int:
        return 7 - self.level

    @classmethod
    def bulk_create(cls, webpage: BookmarkWebpage, headers: list[dict]):
        header_objects = []

        for headers_dict in headers:
            for header, texts in headers_dict.items():
                level = int(header.strip('h'))  # [1-6]

                for text in texts:
                    header_objects.append(
                        cls(webpage=webpage, text=text, level=level)
                    )

        return cls.objects.bulk_create(header_objects)
