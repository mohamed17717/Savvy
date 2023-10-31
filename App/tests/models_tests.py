import json

from django.test import TestCase
from django.db.models import signals
from django.dispatch import Signal
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from App import models


User = get_user_model()


def disconnect_signals(model):
    all_signals_names = filter(lambda i: i.startswith(
        'post') or i.startswith('pre'), dir(signals))
    all_signals = map(lambda name: getattr(signals, name), all_signals_names)

    for signal in all_signals:
        for receiver_func in Signal._live_receivers(signal, sender=model):
            signal.disconnect(receiver_func, sender=model)


class ObjFactory:
    @staticmethod
    def create_user(username=None):
        if username is None:
            username = 'testuser'

        user = User.objects.create_user(
            username=username,
            password=username,
            email=f'{username}@gmail.com',
        )
        return user

    @staticmethod
    def create_file(file_type, how_many=1):
        url = 'https://quotes.toscrape.com/'
        urls = [url for _ in range(how_many)]

        if file_type == 'json':
            data = json.dumps(urls, ensure_ascii=False)

        elif file_type == 'html':
            def get_html_url(
            ): return f'<DT><A HREF="{url}" ADD_DATE="xxx" LAST_MODIFIED="xxx" ICON_URI="https://xds.com/" ICON="xxxx">Text title</A>'
            html_urls = '\n'.join([get_html_url() for _ in range(how_many)])
            data = f'''
                <!DOCTYPE NETSCAPE-Bookmark-file-1><TITLE>Bookmarks</TITLE><H1>Bookmarks Menu</H1>
                <DL><p>{html_urls}</DL></p>
            '''

        else:  # normal txt
            data = '\n'.join(urls)

        return SimpleUploadedFile(f'test_file.{file_type}', data.encode('utf8'))

    @staticmethod
    def create_bookmark_file(**kwargs):
        _file = models.BookmarkFile(**kwargs)
        _file.save()
        return _file


class BookmarkFileTestCase(TestCase):
    model = models.BookmarkFile

    def setUp(self) -> None:
        disconnect_signals(self.model)

        json_file = ObjFactory.create_file('json', 1)
        html_file = ObjFactory.create_file('html', 1)

        user = ObjFactory.create_user()

        self.html_obj = ObjFactory.create_bookmark_file(
            user=user, location=html_file)
        self.json_obj = ObjFactory.create_bookmark_file(
            user=user, location=json_file)
        self.user = user

    def test_create_wrong_file(self):
        with self.assertRaises(ValidationError):
            text_file = ObjFactory.create_file('txt', 1)
            ObjFactory.create_bookmark_file(user=self.user, location=text_file)

    def test_path_property(self):
        self.assertRegex(self.html_obj.path, r'^(.+)\/([^\/]+)\.html$')
        self.assertRegex(self.json_obj.path, r'^(.+)\/([^\/]+)\.json$')

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
        self.assertIsInstance(self.html_obj.bookmarks_links[0].get('url'), str)

        self.assertIsInstance(self.json_obj.bookmarks_links, list)
        self.assertIsInstance(self.json_obj.bookmarks_links[0], dict)
        self.assertIsInstance(self.json_obj.bookmarks_links[0].get('url'), str)


