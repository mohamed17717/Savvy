import urllib3
import requests
import secrets
import uuid
from datetime import timedelta

from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files import File
from django.utils import timezone

from crawler import settings as scrapy_settings

from common.utils.model_utils import FileSizeValidator, clone, bulk_clone
from common.utils.file_utils import hash_file, random_filename
from common.utils.image_utils import compress_image, resize_image, download_image
from common.utils.array_utils import unique_dicts_in_list
from common.utils.url_utils import url_builder

from App import choices, controllers, managers, flows, tasks

from realtime.common.redis_utils import RedisPubSub

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
    def bookmarks_links(self) -> list[dict]:
        file_obj = self.file_obj
        file_obj.validate(raise_exception=True)

        return file_obj.get_links()

    def cleaned_bookmarks_links(self) -> list[dict]:
        # remove duplication from bookmarks (unique on url)
        bookmarks = unique_dicts_in_list(self.bookmarks_links, 'url')
        # get only new bookmarks for this user
        stored_bookmarks = set(
            self.user.bookmarks.all().values_list('url', flat=True))
        bookmarks = [b for b in bookmarks if b['url'] not in stored_bookmarks]
        # clone from other users if any of those bookmarks are exist and fresh to save time
        other_users_bookmarks = Bookmark.objects.exclude(user=self.user).filter(
            url__in=[b['url'] for b in bookmarks],
            process_status__gte=Bookmark.ProcessStatus.TEXT_PROCESSED.value,
            scrapes__created_at__gte=timezone.now() - timedelta(days=100),
        ).distinct('url')
        other_users_urls = set(
            other_users_bookmarks.values_list('url', flat=True))
        bookmarks = [b for b in bookmarks if b['url'] not in other_users_urls]

        # clone bookmarks
        tasks.deep_clone_bookmarks_task(
            [b.id for b in other_users_bookmarks], self.user.id, self.id)

        return bookmarks

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
    ProcessStatus = choices.BookmarkProcessStatusChoices
    UserStatus = choices.BookmarkUserStatusChoices

    # Relations
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='bookmarks'
    )
    parent_file = models.ForeignKey(
        'App.BookmarkFile', on_delete=models.CASCADE,
        related_name='bookmarks', blank=True, null=True
    )

    website = models.ForeignKey(
        'App.Website', on_delete=models.SET_NULL,
        related_name='bookmarks', blank=True, null=True
    )

    # TODO make url and title max length shorter
    # Required
    url = models.URLField(max_length=2048)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False,
                            blank=True, null=True, unique=True, db_index=True)

    # Optionals
    title = models.CharField(max_length=2048, blank=True, null=True)
    more_data = models.JSONField(blank=True, null=True)
    image = models.ImageField(
        upload_to='bookmarks/images/', blank=True, null=True)
    image_url = models.URLField(max_length=2048, blank=True, null=True)

    # Defaults
    process_status = models.PositiveSmallIntegerField(
        default=ProcessStatus.CREATED.value,
        choices=ProcessStatus.choices)
    user_status = models.PositiveSmallIntegerField(
        default=UserStatus.PENDING.value,
        choices=UserStatus.choices)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = managers.BookmarkQuerySet.as_manager()

    def __str__(self) -> str:
        return f'{self.id} - {self.url}'

    # Computed
    @property
    def domain(self) -> str:
        # domain with subdomains
        url = urllib3.util.parse_url(self.url)
        return '.'.join(url.host.split('.')[-2:])

    @property
    def site_name(self) -> str:
        return self.domain.split('.')[-2]

    @property
    def webpage(self):
        return self.webpages.order_by('-id').first()

    @property
    def word_vector(self) -> dict:
        weighting_serializer = self.hooks.get_weighting_serializer()
        return weighting_serializer(self).total_weight

    @property
    def important_words(self) -> dict:
        qs = self.words_weights.filter(important=True)
        return dict(qs.values_list('word', 'weight'))

    @property
    def hooks(self):
        from App.flows.default import BookmarkHooks
        hook_class = BookmarkHooks
        for h in flows.get_flows():
            if h.DOMAIN == self.domain:
                hook_class = h
                break
        return hook_class(self)

    def calculate_important_words(self, word_vector: dict = None) -> dict:
        if word_vector is None:
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
    def store_word_vector(self, commit=True):
        from . import WordWeight
        # Delete the old data , store new ones
        with transaction.atomic():
            self.words_weights.all().delete()

            word_vector = self.word_vector
            important_words = self.calculate_important_words(word_vector)

            words_weights = [
                WordWeight(
                    bookmark=self, word=word, weight=weight,
                    important=word in important_words
                )
                for word, weight in word_vector.items()
            ]
            if commit:
                results = WordWeight.objects.bulk_create(
                    words_weights, batch_size=250)
            else:
                return words_weights

        return results

    def store_tags(self):
        from App.models import Tag

        words = self.important_words

        with transaction.atomic():
            existing_tags = Tag.objects.select_for_update().filter(name__in=words.keys())
            for tag in existing_tags:
                tag.weight += words.pop(tag.name, 0)

            Tag.objects.bulk_update(existing_tags, ['weight'], batch_size=250)

            new_tags = [
                Tag(name=word, weight=weight, user=self.user) for word, weight in words.items()
            ]
            # NOTE - bulk_create will ignore conflicts
            # which will make some tags lost some of the weights
            new_tags = Tag.objects.bulk_create(
                new_tags, batch_size=250, ignore_conflicts=True)

            all_tags = [*existing_tags, *new_tags]
            transaction.on_commit(lambda: self.tags.add(
                *Tag.objects.filter(name__in=self.important_words.keys())
            ))

        return all_tags

    def set_image_from_url(self, url: str, new_width: int = 300):
        url = url_builder(url, self.domain)
        try:
            content, url = download_image(url)
        except requests.exceptions.HTTPError as e:
            if str(e).startswith('429'):
                # Too many requests error, so schedule for later
                from App import tasks
                tasks.schedule_store_bookmark_image_task.delay(self.id, url)
                return
            raise e

        if content is None:
            return

        image = resize_image(content, new_width)
        image = compress_image(image)
        image = ContentFile(image)

        file_name = f'{secrets.token_hex(12)}.jpeg'

        self.image_url = url
        self.image.save(file_name, image, save=True)
        self.save(update_fields=['image_url'])

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
            new_bookmark = clone(self, uuid=uuid.uuid4().hex)
            new_bookmark.user = user
            new_bookmark.parent_file = parent_file
            new_bookmark.user_status = self.UserStatus.PENDING.value
            new_bookmark.save(
                update_fields=['user', 'parent_file', 'user_status'])

            new_bookmark.update_process_status(self.ProcessStatus.CLONED.value)

            if self.webpage:
                new_webpage = clone(self.webpage)
                new_webpage.bookmark = new_bookmark
                new_webpage.save(update_fields=['bookmark'])

                bulk_clone(self.webpage.meta_tags.all(),
                           {'webpage': new_webpage})
                bulk_clone(self.webpage.headers.all(),
                           {'webpage': new_webpage})

            bulk_clone(self.words_weights.all(), {'bookmark': new_bookmark})

            new_bookmark.store_tags()

        return new_bookmark

    def update_process_status(self, new_status):
        if self.process_status >= new_status:
            return

        self.process_status = new_status
        self.save(update_fields=['process_status'])

        RedisPubSub.pub({
            'type': RedisPubSub.MessageTypes.BOOKMARK_CHANGE,
            'user_id': self.user.id,
            'bookmark_id': self.id,
            'status': new_status
        })


class BookmarkHistory(models.Model):
    bookmark = models.ForeignKey(
        'App.Bookmark', on_delete=models.CASCADE, related_name='history'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class Website(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='websites')
    domain = models.URLField()
    favicon = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'domain')

    def __str__(self):
        return f'{self.id} - {self.domain}'


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
            if isinstance(content, str):
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
