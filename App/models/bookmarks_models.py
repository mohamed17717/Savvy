import secrets
import uuid

import requests
import urllib3
from django.contrib.auth import get_user_model
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.validators import (
    FileExtensionValidator,
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models, transaction

from App import choices, controllers, flows, managers, tasks
from common.utils.file_utils import hash_file, random_filename
from common.utils.image_utils import compress_image, download_image, resize_image
from common.utils.model_utils import FileSizeValidator, bulk_clone, clone
from common.utils.time_utils import fromtimestamp
from common.utils.url_utils import url_builder
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
        User, on_delete=models.CASCADE, related_name="bookmark_files"
    )

    # Required
    location = models.FileField(
        upload_to="users/bookmarks/",
        validators=[FileExtensionValidator(["html", "json"]), FileSizeValidator(20)],
    )

    file_hash = models.CharField(max_length=64, blank=True, null=True, editable=False)

    # Analytics
    total_links_count = models.PositiveIntegerField(blank=True, null=True)
    succeeded_links_count = models.PositiveIntegerField(blank=True, null=True)
    failed_links_count = models.PositiveIntegerField(blank=True, null=True)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "file_hash")

    def __str__(self):
        return self.location.name

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
        return self.location.read().decode("utf8")

    @property
    def is_html(self) -> bool:
        return self.path.endswith(".html")

    @property
    def is_json(self) -> bool:
        return self.path.endswith(".json")

    @property
    def file_manager(self) -> controllers.BookmarkFileManager:
        manager = None
        if self.is_html:
            manager = controllers.BookmarkHTMLFileManager
        elif self.is_json:
            manager = controllers.BookmarkJSONFileManager

        if manager is None:
            raise ValidationError("Can't get the file manager")

        return manager

    @property
    def file_obj(self) -> controllers.BookmarkFileManager:
        self.location.seek(0)
        return self.file_manager(self.location)

    @property
    def bookmarks_links(self) -> list[dict]:
        file_obj = self.file_obj
        return file_obj.get_links()

    def cleaned_bookmarks_links(self) -> list[dict]:
        # remove duplication from bookmarks (unique on url)
        new_bookmarks_map = {b["url"]: b for b in self.bookmarks_links}
        new_urls = set(new_bookmarks_map.keys())

        # get only new bookmarks for this user
        stored_urls = set(self.user.bookmarks.only("url").values_list("url", flat=True))

        new_urls -= stored_urls
        del stored_urls

        # clone from other users if any of those
        # bookmarks are exist and fresh to save time
        # others_bookmarks = (
        #     Bookmark.objects
        #     .exclude(user=self.user)
        #     .filter(
        #         url__in=new_urls,
        #         process_status__gte=Bookmark.ProcessStatus.TEXT_PROCESSED.value,
        #         # TODO created in last 100 day disabled for now
        #         # scrapes__created_at__gte=timezone.now() - timedelta(days=100)
        #     )
        #     .values('url', 'id')
        #     .distinct('url')
        # )
        # others_bookmarks_urls = set(
        #     others_bookmarks.values_list('url', flat=True))

        # new_urls -= others_bookmarks_urls

        # clone bookmarks
        # others_ids = []
        # more_data_for_clone = []
        # for others_bookmark in others_bookmarks:
        #     others_ids.append(others_bookmark['id'])
        #     more_data_for_clone.append(new_bookmarks_map[others_bookmark['url']])

        # tasks.deep_clone_bookmarks_task(
        #     others_ids, self.user.id, self.id, more_data_for_clone)
        return list({url: new_bookmarks_map[url] for url in new_urls}.values())

    def init_bookmark(self, data):
        url = data.pop("url")
        title = data.pop("title", None)
        added_at = data.pop("added_at", None)
        if added_at:
            added_at = fromtimestamp(added_at)

        data = data or {}

        return Bookmark(
            user=self.user,
            parent_file=self,
            url=url,
            title=title,
            more_data=data,
            added_at=added_at,
        )


class Bookmark(models.Model):
    """Main bookmark that got clustered and the whole next flow depend on it
    ON_CREATE
        - call the scraper controller to scrape and get webpages / log response
    ACTIONS
        - CUD operations happened internally -- just (R)ead
    """

    ProcessStatus = choices.BookmarkProcessStatusChoices

    # Relations
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookmarks")
    parent_file = models.ForeignKey(
        "App.BookmarkFile",
        on_delete=models.CASCADE,
        related_name="bookmarks",
        blank=True,
        null=True,
    )

    website = models.ForeignKey(
        "App.Website",
        on_delete=models.SET_NULL,
        related_name="bookmarks",
        blank=True,
        null=True,
    )

    # TODO make url and title max length shorter
    # Required
    url = models.URLField(max_length=2048)
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        blank=True,
        null=True,
        unique=True,
        db_index=True,
    )

    # Optionals
    title = models.CharField(max_length=2048, blank=True, null=True)
    more_data = models.JSONField(blank=True, null=True)
    image = models.ImageField(upload_to="bookmarks/images/", blank=True, null=True)
    image_url = models.URLField(max_length=2048, blank=True, null=True)

    # Defaults
    process_status = models.PositiveSmallIntegerField(
        default=ProcessStatus.CREATED.value, choices=ProcessStatus.choices
    )

    favorite = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)
    delete_scheduled_at = models.DateTimeField(blank=True, null=True)
    added_at = models.DateTimeField(blank=True, null=True)

    search_vector = SearchVectorField(blank=True, null=True)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = managers.BookmarkManager()
    hidden_objects = managers.BookmarkHiddenManager()
    all_objects = managers.AllBookmarkManager()

    class Meta:
        indexes = [GinIndex(fields=["search_vector"])]

    def __str__(self) -> str:
        return f"{self.id} - {self.url}"

    # Computed
    @property
    def domain(self) -> str:
        # domain with subdomains
        url = urllib3.util.parse_url(self.url)
        # return '.'.join(url.host.split('.')[-2:])
        host = url.host
        if host.startswith("www."):
            host = host[4:]
        elif host.startswith("m.facebook"):
            host = host[2:]

        return host

    @property
    def site_name(self) -> str:
        return self.domain.split(".")[-2]

    @property
    def webpage(self):
        return self.webpages.order_by("-id").first()

    @property
    def word_vector(self) -> dict:
        weighting_serializer = self.hooks.get_weighting_serializer()
        return weighting_serializer(self).total_weight

    @property
    def important_words(self) -> dict:
        qs = self.words_weights.filter(important=True)
        return dict(qs.values_list("word", "weight"))

    @property
    def hooks(self):
        from App.flows.default import BookmarkHooks

        hook_class = next(
            (h for h in flows.get_flows() if self.domain.endswith(h.DOMAIN)),
            BookmarkHooks,
        )
        return hook_class(self)

    def calculate_important_words(self, word_vector: dict = None) -> dict:
        if word_vector is None:
            word_vector = self.word_vector

        top_weights_ranks = 5
        weights = sorted(set(word_vector.values()), reverse=True)

        if len(weights) > top_weights_ranks:
            break_point = weights[top_weights_ranks - 1]
            word_vector = {k: v for k, v in word_vector.items() if v >= break_point}
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
                    bookmark=self,
                    word=word[:64],
                    weight=weight,
                    important=word in important_words,
                )
                for word, weight in word_vector.items()
            ]
            if commit:
                results = WordWeight.objects.bulk_create(words_weights, batch_size=250)
            else:
                return words_weights

        return results

    def store_tags(self):
        from App.models import Tag

        words = self.important_words

        with transaction.atomic():
            all_tags = self._extracted_from_store_tags_7(Tag, words)
        return all_tags

    # TODO Rename this here and in `store_tags`
    def _extracted_from_store_tags_7(self, Tag, words):
        existing_tags = Tag.objects.select_for_update().filter(name__in=words.keys())
        for tag in existing_tags:
            tag.weight += words.pop(tag.name, 0)

        Tag.objects.bulk_update(existing_tags, ["weight"], batch_size=250)

        new_tags = [
            Tag(name=word, weight=weight, user=self.user)
            for word, weight in words.items()
        ]
        # NOTE - bulk_create will ignore conflicts
        # which will make some tags lost some of the weights
        new_tags = Tag.objects.bulk_create(
            new_tags, batch_size=250, ignore_conflicts=True
        )

        result = [*existing_tags, *new_tags]
        transaction.on_commit(
            lambda: self.tags.add(
                *Tag.objects.filter(name__in=self.important_words.keys())
            )
        )

        return result

    def set_image_from_url(self, url: str, new_width: int = 300):
        url = url_builder(url, self.domain)
        try:
            content, url = download_image(url)
        except requests.exceptions.HTTPError as e:
            if str(e).startswith("429"):
                # Too many requests error, so schedule for later
                tasks.schedule_store_bookmark_image_task.delay(self.id, url)
                return
            raise e

        if content is None:
            return

        image = resize_image(content, new_width)
        image = compress_image(image)
        image = ContentFile(image)

        file_name = f"{secrets.token_hex(12)}.jpeg"

        self.image_url = url
        self.image.save(file_name, image, save=True)
        self.save(update_fields=["image_url"])

    def deep_clone(self, user, parent_file=None, **kwargs):
        """Clone bookmark with all relations for new user
        relations are ->
            - webpages -> meta tags / headers
            - words_weights
            - tags

        new parameters ->
            - user
            - parent file

        update field ->
            - status to PENDING
        """
        with transaction.atomic():
            new_bookmark = clone(self, uuid=uuid.uuid4().hex)
            new_bookmark.user = user
            new_bookmark.parent_file = parent_file

            new_bookmark.favorite = False
            new_bookmark.hidden = False
            new_bookmark.delete_scheduled_at = None
            new_bookmark.added_at = None

            for k, v in kwargs.items():
                setattr(new_bookmark, k, v)

            new_bookmark.save()
            new_bookmark.update_process_status(self.ProcessStatus.CLONED.value)

            if self.webpage:
                new_webpage = clone(self.webpage)
                new_webpage.bookmark = new_bookmark
                new_webpage.save(update_fields=["bookmark"])

                bulk_clone(self.webpage.meta_tags.all(), {"webpage": new_webpage})
                bulk_clone(self.webpage.headers.all(), {"webpage": new_webpage})

            if self.website and self.webpage:
                new_website, _ = Website.objects.get_or_create(
                    user=user,
                    domain=self.website.domain,
                    defaults={"favicon": self.website.favicon},
                )
                new_bookmark.website = new_website
                new_webpage.save(update_fields=["website"])

            bulk_clone(self.words_weights.all(), {"bookmark": new_bookmark})

            new_bookmark.store_tags()

        return new_bookmark

    def update_process_status(self, new_status):
        if self.process_status >= new_status:
            return

        self.process_status = new_status
        self.save(update_fields=["process_status"])

        RedisPubSub.pub(
            {
                "type": RedisPubSub.MessageTypes.BOOKMARK_CHANGE,
                "user_id": self.user.id,
                "bookmark_id": self.id,
                "status": new_status,
            }
        )


class BookmarkHistory(models.Model):
    bookmark = models.ForeignKey(
        "App.Bookmark", on_delete=models.CASCADE, related_name="history"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.id} - {self.bookmark.url}"


class Website(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="websites")
    domain = models.URLField()
    favicon = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("user", "domain")

    def __str__(self):
        return f"{self.id} - {self.domain}"


class ScrapyResponseLog(models.Model):
    # Relations
    bookmark = models.ForeignKey(
        "App.Bookmark", on_delete=models.CASCADE, related_name="scrapes"
    )
    # Required
    status_code = models.PositiveSmallIntegerField()

    # Optional
    html_file = models.FileField(
        upload_to="scrape/html/",
        validators=[
            FileExtensionValidator(["html"]),
            FileSizeValidator(5),
        ],
        blank=True,
        null=True,
    )
    error = models.TextField(blank=True, null=True)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id} - [{self.status_code}] -> ({self.bookmark.url})"

    def store_file(self, content):
        dir_path = self.html_file.field.upload_to
        file_path = random_filename(dir_path, "html")
        file_name = file_path.split("/")[-1]

        self.html_file = ContentFile(content, name=file_name)
        self.save(update_fields=["html_file"])

        return file_path


class BookmarkWebpage(models.Model):
    # Relations
    bookmark = models.ForeignKey(
        "App.Bookmark", on_delete=models.CASCADE, related_name="webpages"
    )

    # Required
    title = models.CharField(max_length=2048)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} - {self.title}"


class WebpageMetaTag(models.Model):
    # Relations
    webpage = models.ForeignKey(
        "App.BookmarkWebpage", on_delete=models.CASCADE, related_name="meta_tags"
    )

    # Required
    # TODO make it 64 when cleaner work fine
    name = models.CharField(max_length=2048, default="undefined")
    content = models.TextField(blank=True, null=True)

    # Optional
    attrs = models.JSONField(blank=True, null=True)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} - {self.name}"

    @property
    def weight_factor(self) -> int:
        # TODO make sure name saved lower case and without and colon prefix or suffix
        name = self.name.lower().split(":")[-1]
        factors_map = {
            # Web and SEO Metadata
            "site": 2,
            "apple-mobile-web-app-title": 1,
            "tweetmeme-title": 1,
            "alt": 3,
            "application-name": 1,
            "site_name": 2,
            "handheldfriendly": 1,
            "description": 5,
            "keywords": 5,
            "news_keywords": 5,
            # Content Identification and Description
            "name": 4,
            "title": 5,
            "summary": 5,
            "subtitle": 4,
            "topic": 5,
            "subject": 4,
            "category": 4,
            "classification": 3,
            "type": 3,
            "medium": 3,
            "coverage": 3,
            "distribution": 2,
            "directory": 2,
            "pagename": 4,
            "rating": 2,
            "target": 3,
            # Authorship and Ownership
            "artist": 3,
            "author": 4,
            "creator": 4,
            "designer": 3,
            "owner": 2,
            "copyright": 1,
        }

        return factors_map.get(name, 1)

    @classmethod
    def bulk_create(cls, webpage: BookmarkWebpage, tags: list[dict]):
        tag_objects = [
            cls(
                webpage=webpage,
                name=tag.get("name", "UNKNOWN"),
                content=tag.get("content"),
                attrs=tag,
            )
            for tag in tags
        ]
        return cls.objects.bulk_create(tag_objects)


class WebpageHeader(models.Model):
    webpage = models.ForeignKey(
        "App.BookmarkWebpage", on_delete=models.CASCADE, related_name="headers"
    )

    # Required
    text = models.TextField()
    level = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(6)]
    )

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} - {self.text}"

    @property
    def tagname(self) -> str:
        return f"h{self.level}"

    @property
    def weight_factor(self) -> int:
        return {"h1": 9, "h2": 7, "h3": 4, "h4": 3, "h5": 2, "h6": 1}.get(
            self.tagname, 1
        )

    @classmethod
    def bulk_create(cls, webpage: BookmarkWebpage, headers: list[dict]):
        header_objects = []

        for headers_dict in headers:
            for header, texts in headers_dict.items():
                level = int(header.strip("h"))  # [1-6]

                header_objects.extend(
                    cls(webpage=webpage, text=text, level=level) for text in texts
                )
        return cls.objects.bulk_create(header_objects)
