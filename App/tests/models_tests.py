import json
import random
import string
from datetime import timedelta
from time import sleep

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Sum, signals
from django.dispatch import Signal
from django.test import TestCase

from App import models

User = get_user_model()


def disconnect_signals(model):
    disconnected_receivers = []

    # Identifying the signals to disconnect
    all_signals_names = filter(
        lambda i: i.startswith("post") or i.startswith("pre"), dir(signals)
    )
    all_signals = map(lambda name: getattr(signals, name), all_signals_names)

    # Disconnecting the signals and storing the receivers
    for signal in all_signals:
        for receiver_func in Signal._live_receivers(signal, sender=model):
            signal.disconnect(receiver_func, sender=model)
            disconnected_receivers.append((signal, receiver_func))

    # Closure to reconnect the signals
    def reconnect():
        for signal, receiver_func in disconnected_receivers:
            signal.connect(receiver_func, sender=model)

    return reconnect


class ObjFactory:
    @staticmethod
    def create_user(username=None):
        if username is None:
            username = "testuser"

        return User.objects.create_user(
            username=username,
            password=username,
            email=f"{username}@gmail.com",
        )

    @staticmethod
    def create_file(file_type, how_many=1):
        url = "https://quotes.toscrape.com/"
        urls = [url for _ in range(how_many)]

        if file_type == "json":
            data = json.dumps(urls, ensure_ascii=False)

        elif file_type == "html":

            def get_html_url():
                return f'<DT><A HREF="{url}" ADD_DATE="xxx" LAST_MODIFIED="xxx" ICON_URI="https://xds.com/" ICON="xxxx">Text title</A>'  # noqa

            html_urls = "\n".join([get_html_url() for _ in range(how_many)])
            data = f"""
                <!DOCTYPE NETSCAPE-Bookmark-file-1>
                <TITLE>Bookmarks</TITLE>
                <H1>Bookmarks Menu</H1>
                <DL><p>{html_urls}</DL></p>
            """

        else:  # normal txt
            data = "\n".join(urls)

        return SimpleUploadedFile(f"test_file.{file_type}", data.encode("utf8"))

    @staticmethod
    def create_bookmark_file(user, location, **kwargs):
        _file = models.BookmarkFile(user=user, location=location, **kwargs)
        _file.save()
        return _file

    @staticmethod
    def create_bookmark(user, url, **kwargs):
        bm = models.Bookmark(user=user, url=url, **kwargs)
        bm.save()
        return bm

    @staticmethod
    def create_bookmark_webpage(bookmark, title, **kwargs):
        return models.BookmarkWebpage.objects.create(bookmark=bookmark, title=title)

    @staticmethod
    def create_dummy_bookmark_file(user):
        return ObjFactory.create_bookmark_file(
            user=user, location=ObjFactory.create_file("json")
        )


class BookmarkFileTestCase(TestCase):
    model = models.BookmarkFile

    def setUp(self) -> None:
        self.reconnect_signals = disconnect_signals(self.model)

        json_file = ObjFactory.create_file("json", 1)
        html_file = ObjFactory.create_file("html", 1)

        user = ObjFactory.create_user()

        self.html_obj = ObjFactory.create_bookmark_file(user=user, location=html_file)
        self.json_obj = ObjFactory.create_bookmark_file(user=user, location=json_file)
        self.user = user

    def tearDown(self) -> None:
        self.reconnect_signals()

    def test_create_wrong_file(self):
        with self.assertRaises(ValidationError):
            text_file = ObjFactory.create_file("txt", 1)
            ObjFactory.create_bookmark_file(user=self.user, location=text_file)

    def test_path_property(self):
        self.assertRegex(self.html_obj.path, r"^(.+)\/([^\/]+)\.html$")
        self.assertRegex(self.json_obj.path, r"^(.+)\/([^\/]+)\.json$")

    def test_file_content_property(self):
        self.assertIsInstance(self.html_obj.file_content, str)
        # json valid
        self.assertIsInstance(json.loads(self.json_obj.file_content), list)

    def test_is_html_property(self):
        self.assertTrue(self.html_obj.is_html)
        self.assertFalse(self.json_obj.is_html)

    def test_is_json_property(self):
        self.assertFalse(self.html_obj.is_json)
        self.assertTrue(self.json_obj.is_json)

    def test_file_manager_property(self):
        self.assertIs(self.html_obj.file_manager, models.BookmarkHTMLFileManager)
        self.assertIs(self.json_obj.file_manager, models.BookmarkJSONFileManager)

    def test_file_obj_property(self):
        self.assertIsInstance(self.html_obj.file_obj, models.BookmarkHTMLFileManager)
        self.assertIsInstance(self.json_obj.file_obj, models.BookmarkJSONFileManager)

    def test_bookmarks_links_property(self):
        # list of dicts contain urls
        self.assertIsInstance(self.html_obj.bookmarks_links, list)
        self.assertIsInstance(self.html_obj.bookmarks_links[0], dict)
        self.assertIsInstance(self.html_obj.bookmarks_links[0].get("url"), str)

        self.assertIsInstance(self.json_obj.bookmarks_links, list)
        self.assertIsInstance(self.json_obj.bookmarks_links[0], dict)
        self.assertIsInstance(self.json_obj.bookmarks_links[0].get("url"), str)


class BookmarkTestCase(TestCase):
    model = models.Bookmark

    def setUp(self) -> None:
        self.reconnect_signals = disconnect_signals(self.model)
        self.reconnect_signals_bm_file = disconnect_signals(models.BookmarkFile)

        self.url = "https://quotes.toscrape.com/"
        self.user = ObjFactory.create_user()
        self.obj = ObjFactory.create_bookmark(user=self.user, url=self.url)

    def tearDown(self) -> None:
        self.reconnect_signals()
        self.reconnect_signals_bm_file()

    def test_domain_property(self):
        self.assertEqual(self.obj.domain, "quotes.toscrape.com")

    def test_site_name_property(self):
        self.assertEqual(self.obj.site_name, "toscrape")

    def test_instance_by_parent_class_method(self):
        data = {
            "url": "https://quotes.toscrape.com/",
            "title": "this is test url",
            "more": "this is more data",
        }
        bookmark_file = ObjFactory.create_bookmark_file(
            user=self.user, location=ObjFactory.create_file("json", 5)
        )
        obj = self.model.instance_by_parent(bookmark_file, data.copy())

        self.assertIs(obj.parent_file, bookmark_file)
        self.assertEqual(obj.url, data["url"])
        self.assertEqual(obj.title, data["title"])
        self.assertDictEqual(obj.more_data, {"more": "this is more data"})


class ScrapyResponseLogTestCase(TestCase):
    model = models.ScrapyResponseLog

    def setUp(self) -> None:
        self.reconnect_signals = disconnect_signals(self.model)

        self.url = "https://quotes.toscrape.com/"
        self.obj = self.model.objects.create(status_code=200)

    def tearDown(self) -> None:
        self.reconnect_signals()

    def test_store_file_method(self):
        content = "this is content"
        self.obj.store_file(content)

        with open(self.obj.html_file.path) as f:
            self.assertEqual(f.read(), content)

    def test_is_url_exists_class_method(self):
        self.assertTrue(self.obj.is_url_exists(self.url))

        # expire it and check the exist after expiration
        # self.obj.LIFE_LONG = timedelta(seconds=2)
        sleep(1.5)
        self.assertFalse(self.obj.is_url_exists(self.url, timedelta(seconds=1)))


class BookmarkWebpageTestCase(TestCase):
    # NOTE no methods or property
    model = models.BookmarkWebpage

    def setUp(self) -> None:
        self.reconnect_signals = disconnect_signals(self.model)
        self.reconnect_signals_bm = disconnect_signals(models.Bookmark)

        self.url = "https://quotes.toscrape.com/"
        self.title = "this is title"
        self.user = ObjFactory.create_user()
        self.bookmark = ObjFactory.create_bookmark(user=self.user, url=self.url)

        self.webpage = ObjFactory.create_bookmark_webpage(
            bookmark=self.bookmark, title=self.title
        )

    def tearDown(self) -> None:
        self.reconnect_signals()
        self.reconnect_signals_bm()


class WebpageMetaTagTestCase(TestCase):
    model = models.WebpageMetaTag

    def setUp(self) -> None:
        self.reconnect_signals = disconnect_signals(self.model)

        wb = BookmarkWebpageTestCase()
        wb.setUp()

        self.wb = wb
        self.name = "name"
        self.content = "yes, this is meta_tag"
        self.obj = self.model.objects.create(
            webpage=wb.webpage, name=self.name, content=self.content
        )

    def tearDown(self) -> None:
        self.reconnect_signals()
        self.wb.tearDown()

    def test_weight_factor_property(self):
        obj = self.obj
        self.assertEqual(obj.weight_factor, 4)

        obj.name = "keywords"
        self.assertEqual(obj.weight_factor, 5)

    def test_bulk_create_class_method(self):
        # just run to make sure not raise errors
        old_count = self.wb.webpage.meta_tags.count()
        self.model.bulk_create(
            self.wb.webpage,
            tags=[
                {"name": "keywords", "content": "one, two, three"},
                {"name": "name", "content": "one, two, three"},
                {"name": "pla pla pla", "content": "one, two, three"},
            ],
        )
        self.assertEqual(self.wb.webpage.meta_tags.count(), old_count + 3)


class WebpageHeaderTestCase(TestCase):
    model = models.WebpageHeader

    def setUp(self) -> None:
        self.reconnect_signals = disconnect_signals(self.model)

        wb = BookmarkWebpageTestCase()
        wb.setUp()

        self.wb = wb
        self.text = "yes, this is meta_tag"
        self.level = 1
        self.obj = self.model.objects.create(
            webpage=wb.webpage, text=self.text, level=self.level
        )

    def tearDown(self) -> None:
        self.reconnect_signals()
        self.wb.tearDown()

    def test_tagname_property(self):
        self.assertEqual(self.obj.tagname, "h1")

    def test_bulk_create_class_method(self):
        # just run to make sure not raise errors
        old_count = self.wb.webpage.headers.count()
        self.model.bulk_create(
            self.wb.webpage,
            headers=[
                {"h1": ["keywords", "content", "one, two, three"]},
                {"h2": ["keywords", "content", "one, two, three"]},
                {"h3": ["keywords", "content", "one, two, three"]},
            ],
        )
        self.assertEqual(self.wb.webpage.headers.count(), old_count + 9)


class TagTestCase(TestCase):
    model = models.Tag

    def setUp(self) -> None:
        self.user = ObjFactory.create_user()
        self.bookmark = ObjFactory.create_bookmark(
            user=self.user, url="https://google.com"
        )

    def deprecated_test_create_word_reflect_tag(self):
        word = "hello"
        # check tag created with word
        tag = models.Tag.objects.filter(user=self.user, name=word)
        self.assertEqual(tag.count(), 1)

        # create again and make sure tag merged not duplicated
        word = "hello"

        tag = models.Tag.objects.filter(user=self.user, name=word)
        self.assertEqual(tag.count(), 1)
