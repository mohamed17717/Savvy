import urllib3
import requests
import secrets
import base64

from django.db import models, transaction
from django.db.models import F
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files import File

from crawler import settings as scrapy_settings

from common.utils.model_utils import FileSizeValidator, clone, bulk_clone
from common.utils.file_utils import hash_file, random_filename
from common.utils.image_utils import compress_image, resize_image

from App import choices, controllers


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

    file_hash = models.CharField(
        max_length=64, blank=True, null=True, editable=False)

    # Analytics
    total_links_count = models.PositiveIntegerField(blank=True, null=True)
    succeeded_links_count = models.PositiveIntegerField(blank=True, null=True)
    failed_links_count = models.PositiveIntegerField(blank=True, null=True)

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
    def file_manager(self) -> controllers.BookmarkFileManager:
        manager = None
        if self.is_html:
            manager = controllers.BookmarkHTMLFileManager
        elif self.is_json:
            manager = controllers.BookmarkJSONFileManager

        if manager is None:
            raise ValidationError('Can\'t get the file manager')

        return manager

    @property
    def file_obj(self) -> controllers.BookmarkFileManager:
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

    # TODO make url and title max length shorter
    # Required
    url = models.URLField(max_length=2048)

    # Optionals
    title = models.CharField(max_length=2048, blank=True, null=True)
    more_data = models.JSONField(blank=True, null=True)
    image = models.ImageField(
        upload_to='bookmarks/images/', blank=True, null=True)
    image_url = models.URLField(max_length=2048, blank=True, null=True)

    # Defaults
    # merge all status with crawled and sim_calculated
    status = models.PositiveSmallIntegerField(
        default=choices.BookmarkStatusChoices.PENDING.value,
        choices=choices.BookmarkStatusChoices.choices)
    crawled = models.BooleanField(default=False)
    similarity_calculated = models.BooleanField(default=False)
    cloned = models.BooleanField(default=False)

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
        qs = self.words_weights.filter(important=True)
        return dict(qs.values_list('word', 'weight'))

    def calculate_important_words(self) -> dict:
        word_vector = self.word_vector

        top_weights_ranks = 5
        weights = sorted(set(word_vector.values()), reverse=True)

        if len(weights) > top_weights_ranks:
            break_point = weights[top_weights_ranks-1]
            word_vector = {
                k: v for k, v in word_vector.items() if v >= break_point
            }
        return word_vector

    # methods
    def store_word_vector(self):
        from . import WordWeight
        # Delete the old data , store new ones
        self.words_weights.all().delete()

        word_vector = self.word_vector
        important_words = set(self.calculate_important_words().keys())

        words_weights = [
            WordWeight(
                bookmark=self, word=word, weight=weight,
                important=word in important_words
            )
            for word, weight in word_vector.items()
        ]

        return WordWeight.objects.bulk_create(words_weights, batch_size=250)

    def store_tags(self):
        from App.models import Tag

        words = self.important_words

        with transaction.atomic():
            existing_tags = Tag.objects.select_for_update().filter(name__in=words.keys())

            for tag in existing_tags:
                tag.weight += F('weight') + words.pop(tag.name, 0)

            Tag.objects.bulk_update(existing_tags, ['weight'], batch_size=250)
            new_tags = [
                Tag(name=word, weight=weight, user=self.user) for word, weight in words.items()
            ]
            # NOTE - bulk_create will ignore conflicts
            # which will make some tags lost some of the weights
            new_tags = Tag.objects.bulk_create(
                new_tags, batch_size=250, ignore_conflicts=True)

        return [*existing_tags, *new_tags]

    def set_image_from_url(self, url: str, new_width: int = 300):
        if url.startswith('data:image'):
            content = base64.b64decode(url.split(',')[-1])
        else:
            if url.startswith('://'):
                url = 'https' + url
            if not url.startswith('http') and not url.startswith('/'):
                url = '/' + url
            if url.startswith('/'):
                url = f'https://{self.domain}' + url

            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            content = response.content

        image = resize_image(content, new_width)
        image = compress_image(image)
        image = ContentFile(image)

        file_name = f'{secrets.token_hex(12)}.jpeg'

        self.image_url = url
        self.image.save(file_name, image, save=True)
        self.save(update_fields=['image_url'])

        return self.image

    def deep_clone(self, user, parent_file=None):
        """Clone bookmark with all relations for new user
        relations are ->
            - webpages -> meta tags / headers
            - words_weights
            - tags

        new parameters ->
            - user
            - parent file

        skip relations ->
            - clusters (because it is not needed for new user)

        update field ->
            - similarity_calculated to False
            - status to PENDING
        """
        with transaction.atomic():
            new_bookmark = clone(self)

            new_bookmark.user = user
            new_bookmark.cloned = True
            new_bookmark.parent_file = parent_file
            new_bookmark.similarity_calculated = False
            new_bookmark.status = choices.BookmarkStatusChoices.PENDING.value
            new_bookmark.save(update_fields=[
                              'user', 'parent_file', 'similarity_calculated', 'status', 'cloned'])

            new_webpage = clone(self.webpage)
            new_webpage.bookmark = new_bookmark
            new_webpage.save(update_fields=['bookmark'])

            bulk_clone(self.webpage.meta_tags.all(), {'webpage': new_webpage})
            bulk_clone(self.webpage.headers.all(), {'webpage': new_webpage})

            bulk_clone(self.words_weights.all(), {'bookmark': new_bookmark})

            new_bookmark.store_tags()

        return new_bookmark

    @classmethod
    def make_clusters(cls, user):
        from App.types import SimilarityMatrixType
        from . import SimilarityMatrix, WordWeight

        # TODO make it db transaction
        # Delete old cluster
        user.clusters.all().delete()

        # Get similarity with old ones in mind
        bookmarks = user.bookmarks.all()
        document_ids, vectors = WordWeight.word_vectors(bookmarks)

        similarity_object = SimilarityMatrix.get_object(user)
        old_similarity = similarity_object.to_type
        similarity = SimilarityMatrixType(vectors, document_ids)

        new_similarity = old_similarity + similarity

        # Clustering
        clusters_objects = controllers.ClusterMaker(
            document_ids, new_similarity.similarity_matrix
        ).make()

        # update similarity file and make bookmarks to done
        bookmarks.update(similarity_calculated=True)
        similarity_object.update_matrix(new_similarity.similarity_matrix)

        return clusters_objects


class ScrapyResponseLog(models.Model):
    # Relations
    bookmark = models.ForeignKey(
        'App.Bookmark', on_delete=models.CASCADE, related_name='scrapes'
    )
    # Required
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

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.id} - [{self.status_code}] -> ({self.bookmark.url})'

    def store_file(self, content):
        file_path = random_filename(scrapy_settings.STORAGE_PATH, 'html')
        with open(file_path, 'wb+') as f:
            if type(content) is str:
                content = content.encode('utf8')

            dj_file = File(f)
            dj_file.write(content)

            self.html_file = dj_file
            self.save(update_fields=['html_file'])

        return file_path


class BookmarkWebpage(models.Model):
    # Relations
    bookmark = models.ForeignKey(
        'App.Bookmark', on_delete=models.CASCADE, related_name='webpages'
    )

    # Required
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

    # Optional
    attrs = models.JSONField(blank=True, null=True)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
