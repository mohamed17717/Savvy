import os
import urllib3
import hashlib
from datetime import timedelta
import numpy as np

from django.db import models, transaction
from django.db.models import QuerySet
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from django.core.files import File
from django.utils import timezone

from crawler import settings as scrapy_settings

from common.utils.model_utils import FileSizeValidator
from common.utils.string_utils import random_string
from common.utils.file_utils import hash_file

from App.controllers import (
    BookmarkFileManager, BookmarkHTMLFileManager, BookmarkJSONFileManager,
    TextCleaner, ClusterMaker, CosineSimilarityCalculator
)


User = get_user_model()


def custom_get_or_create(model, **kwargs):
    # because of normal get_or_create cause issues in concurrency
    # so i updated the flow to make sure its doing things right
    try:
        with transaction.atomic():
            obj, created = model.objects.get_or_create(**kwargs)
            return obj, created
    except IntegrityError:
        # Handle the exception if a duplicate is trying to be created
        obj = model.objects.get(**kwargs)
        return obj, False


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
        upload_to='users/bookmarks/', editable=False,
        validators=[
            FileExtensionValidator(['html', 'json']), FileSizeValidator(5)
        ]
    )

    file_hash = models.CharField(
        max_length=64, blank=True, null=True, editable=False)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'file_hash')

    def save(self, *args, **kwargs):
        self.full_clean()  # To make sure field validators run

        if self.pk is None:
            self.file_hash = hash_file(self.location)

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

    def init_bookmark(self, data):
        url = data.pop('url')
        title = data.pop('title', None)
        data = data or None

        return Bookmark(
            user=self.user, parent_file=self,
            url=url, title=title, more_data=data
        )


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

    # TODO depend on bookmark and remove url
    # TODO make url and title max length shorter
    # Required
    url = models.URLField(max_length=2048)

    # Optionals
    title = models.CharField(max_length=2048, blank=True, null=True)
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
    def word_vector(self) -> dict:
        from App.serializers import BookmarkWeightingSerializer
        return BookmarkWeightingSerializer(self).total_weight

    @property
    def important_words(self) -> dict:
        # word_vector = self.word_vector
        # TODO use important flag in database and filter on it
        word_vector = {
            w['word']: w['weight']
            for w in self.words_weights.all().values('word', 'weight')
        }

        top_weights_ranks = 5
        weights = sorted(set(word_vector.values()))
        if len(weights) > top_weights_ranks:
            weight_break_point = weights[-top_weights_ranks:][0]
            word_vector = filter(
                lambda item: item[1] >= weight_break_point, word_vector.items())
            word_vector = {
                k: v for k, v in word_vector
            }

        return word_vector

    # methods
    def store_word_vector(self):
        from . import DocumentWordWeight
        # Delete the old data , store new ones
        self.words_weights.all().delete()

        word_vector = self.word_vector

        # TODO refactor this code
        top_weights_ranks = 5
        weights = sorted(set(word_vector.values()))
        important_words = word_vector.copy()
        if len(weights) > top_weights_ranks:
            weight_break_point = weights[-top_weights_ranks:][0]
            important_words = filter(
                lambda item: item[1] >= weight_break_point, important_words.items())
            important_words = {
                k: v for k, v in important_words
            }
        important_words = set(important_words.keys())

        words_weights = [
            DocumentWordWeight(
                bookmark=self, word=word, weight=weight, important=word in important_words
            )
            for word, weight in word_vector.items()
        ]

        return DocumentWordWeight.objects.bulk_create(words_weights, batch_size=250)

    def store_tags(self):
        # TODO make this more efficient
        from . import Tag

        tags = []
        for word, weight in self.important_words.items():
            tag, _ = custom_get_or_create(Tag, user=self.user, name=word)

            tag.bookmarks.add(self)
            tag.weight += weight
            tag.save(update_fields=['weight'])

            tags.append(tag)

        return tags

    # shortcuts
    @classmethod
    def cluster_bookmarks(cls, bookmarks: QuerySet['Bookmark']):
        from . import DocumentCluster

        bookmark_id = [b.id for b in bookmarks]
        bookmarks = cls.objects.filter(id__in=bookmark_id)
        # vectors = [b.word_vector for b in bookmarks]
        vectors = [b.important_words for b in bookmarks]

        sim_calculator = CosineSimilarityCalculator(vectors)
        similarity_matrix = sim_calculator.similarity()
        similarity_matrix = np.ceil(similarity_matrix*100)/100

        # Clustering
        clusters_maker = ClusterMaker(bookmark_id, similarity_matrix)
        flat_clusters = clusters_maker.make()

        clusters_qs = [bookmarks.filter(id__in=cluster)
                       for cluster in flat_clusters.value]
        clusters_objects = []
        index = 0
        for cluster, correlation in zip(clusters_qs, flat_clusters.correlation.values()):
            user = cluster[0].user
            cluster_name = f'{index}-threshold-{correlation}-{random_string(4)}'
            cluster_object = DocumentCluster.objects.create(
                user=user, name=cluster_name, correlation=correlation)
            cluster_object.bookmarks.set(cluster)
            clusters_objects.append(cluster_object)
            index += 1

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
    url = models.URLField(max_length=2048)
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

    # TODO depend on bookmark and remove url
    # Required
    url = models.URLField(max_length=2048)
    title = models.CharField(max_length=2048)

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

    def save(self, *args, **kwargs) -> None:
        if self.content:
            self.cleaned_content = TextCleaner(self.content).full_clean().text

        return super().save(*args, **kwargs)

    @property
    def weight_factor(self) -> int:
        # TODO make sure name saved lower case and without and colon prefix or suffix
        name = self.name.lower().split(':')[-1]
        factors_map = {
            # Web and SEO Metadata
            'site': 2,
            'apple-mobile-web-app-title': 1,
            'tweetmeme-title': 1,
            'alt': 3,
            'application-name': 1,
            'site_name': 2,
            'handheldfriendly': 1,
            'description': 5,
            'keywords': 5,
            'news_keywords': 5,

            # Content Identification and Description
            'name': 4,
            'title': 5,
            'summary': 5,
            'subtitle': 4,
            'topic': 5,
            'subject': 4,
            'category': 4,
            'classification': 3,
            'type': 3,
            'medium': 3,
            'coverage': 3,
            'distribution': 2,
            'directory': 2,
            'pagename': 4,
            'rating': 2,
            'target': 3,

            # Authorship and Ownership
            'artist': 3,
            'author': 4,
            'creator': 4,
            'designer': 3,
            'owner': 2,
            'copyright': 1,

        }

        return factors_map.get(name, 1)

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
        return {
            'h1': 9,
            'h2': 7,
            'h3': 4,
            'h4': 3,
            'h5': 2,
            'h6': 1
        }.get(self.tagname, 1)

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
