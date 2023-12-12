import json
import string
import random
from datetime import timedelta
from time import sleep

from django.test import TestCase
from django.db.models import signals, Sum
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
    def create_bookmark_webpage(bookmark, url, title, **kwargs):
        return models.BookmarkWebpage.objects.create(
            bookmark=bookmark, url=url, title=title
        )

    @staticmethod
    def create_dummy_bookmark_file(user):
        return ObjFactory.create_bookmark_file(
            user=user, location=ObjFactory.create_file('json')
        )

    @staticmethod
    def create_cluster(user):
        return models.DocumentCluster.objects.create(
            user=user, name=''.join(random.choices(string.ascii_letters, k=8))
        )


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
        self.assertIs(self.html_obj.file_manager,
                      models.BookmarkHTMLFileManager)
        self.assertIs(self.json_obj.file_manager,
                      models.BookmarkJSONFileManager)

    def test_file_obj_property(self):
        self.assertIsInstance(self.html_obj.file_obj,
                              models.BookmarkHTMLFileManager)
        self.assertIsInstance(self.json_obj.file_obj,
                              models.BookmarkJSONFileManager)

    def test_bookmarks_links_property(self):
        # list of dicts contain urls
        self.assertIsInstance(self.html_obj.bookmarks_links, list)
        self.assertIsInstance(self.html_obj.bookmarks_links[0], dict)
        self.assertIsInstance(self.html_obj.bookmarks_links[0].get('url'), str)

        self.assertIsInstance(self.json_obj.bookmarks_links, list)
        self.assertIsInstance(self.json_obj.bookmarks_links[0], dict)
        self.assertIsInstance(self.json_obj.bookmarks_links[0].get('url'), str)


class BookmarkTestCase(TestCase):
    model = models.Bookmark

    def setUp(self) -> None:
        disconnect_signals(self.model)
        disconnect_signals(models.BookmarkFile)

        self.url = 'https://quotes.toscrape.com/'
        self.user = ObjFactory.create_user()
        self.obj = ObjFactory.create_bookmark(user=self.user, url=self.url)

    def test_domain_property(self):
        self.assertEqual(self.obj.domain, 'quotes.toscrape.com')

    def test_site_name_property(self):
        self.assertEqual(self.obj.site_name, 'toscrape')

    def test_word_vector_property(self):
        # TODO test it for more case and strict data
        vector = self.obj.word_vector
        self.assertIsInstance(vector, dict)
        self.assertIsInstance(list(vector.keys())[0], str)
        self.assertIsInstance(list(vector.values())[0], int)

    def test_important_words_property(self):
        # TODO test it for more case and strict data
        vector = self.obj.important_words
        self.assertIsInstance(vector, dict)
        # TODO create important word for testing
        if vector:
            self.assertIsInstance(list(vector.keys())[0], str)
            self.assertIsInstance(list(vector.values())[0], int)

    def test_store_word_vector_method(self):
        # it depend on word vector property
        length = len(self.obj.word_vector)
        total_weights = sum(self.obj.word_vector.values())
        # words created
        self.obj.store_word_vector()
        self.assertEqual(self.obj.words_weights.count(), length)
        # words not duplicated
        self.obj.store_word_vector()
        self.assertEqual(self.obj.words_weights.count(), length)

        # weights stored right
        total = self.obj.words_weights.all().aggregate(
            total=Sum('weight'))['total']
        self.assertEqual(total, total_weights)

        for word, weight in self.obj.word_vector.items():
            db_weight = self.obj.words_weights.get(word=word).weight
            self.assertEqual(db_weight, weight)

    def test_store_tags_method(self):
        # it depend on word vector property
        length = len(self.obj.important_words)
        total_weights = sum(self.obj.important_words.values())
        # words created
        self.obj.store_tags()
        self.assertEqual(self.obj.tags.count(), length)

        # weights stored right
        # TODO make sure tags are created in tests
        total = self.obj.tags.all().aggregate(
            total=Sum('weight'))['total'] or 0
        self.assertEqual(total, total_weights)

        for word, weight in self.obj.important_words.items():
            db_weight = self.obj.tags.get(name=word).weight
            self.assertEqual(db_weight, weight)

    def test_instance_by_parent_class_method(self):
        data = {
            'url': 'https://quotes.toscrape.com/',
            'title': 'this is test url',
            'more': 'this is more data'
        }
        bookmark_file = ObjFactory.create_bookmark_file(
            user=self.user, location=ObjFactory.create_file('json', 5)
        )
        obj = self.model.instance_by_parent(bookmark_file, data.copy())

        self.assertIs(obj.parent_file, bookmark_file)
        self.assertEqual(obj.url, data['url'])
        self.assertEqual(obj.title, data['title'])
        self.assertDictEqual(obj.more_data, {'more': 'this is more data'})

    def test_cluster_bookmarks_class_method(self):
        # should be refactored
        pass


class ScrapyResponseLogTestCase(TestCase):
    model = models.ScrapyResponseLog

    def setUp(self) -> None:
        disconnect_signals(self.model)

        self.url = 'https://quotes.toscrape.com/'
        self.obj = self.model.objects.create(
            url=self.url,
            status_code=200
        )

    def test_store_file_method(self):
        content = 'this is content'
        self.obj.store_file(content)

        with open(self.obj.html_file.path, 'r') as f:
            self.assertEqual(f.read(), content)

    def test_is_url_exists_class_method(self):
        self.assertTrue(self.obj.is_url_exists(self.url))

        # expire it and check the exist after expiration
        # self.obj.LIFE_LONG = timedelta(seconds=2)
        sleep(1.5)
        self.assertFalse(self.obj.is_url_exists(
            self.url, timedelta(seconds=1)))


class BookmarkWebpageTestCase(TestCase):
    # NOTE no methods or property
    model = models.BookmarkWebpage

    def setUp(self) -> None:
        disconnect_signals(self.model)
        disconnect_signals(models.Bookmark)

        self.url = 'https://quotes.toscrape.com/'
        self.title = 'this is title'
        self.user = ObjFactory.create_user()
        self.bookmark = ObjFactory.create_bookmark(
            user=self.user, url=self.url)

        self.webpage = ObjFactory.create_bookmark_webpage(
            bookmark=self.bookmark, url=self.url, title=self.title
        )


class WebpageMetaTagTestCase(TestCase):
    model = models.WebpageMetaTag

    def setUp(self) -> None:
        disconnect_signals(self.model)

        wb = BookmarkWebpageTestCase()
        wb.setUp()

        self.wb = wb
        self.name = 'name'
        self.content = 'yes, this is meta_tag'
        self.obj = self.model.objects.create(
            webpage=wb.webpage, name=self.name, content=self.content)

    def test_save_method(self):
        # is content cleaned
        self.assertIsNotNone(self.obj.cleaned_content)
        self.assertEqual(self.obj.cleaned_content,  'yes meta tag')

    def test_weight_factor_property(self):
        obj = self.obj
        self.assertEqual(obj.weight_factor, 4)

        obj.name = 'keywords'
        self.assertEqual(obj.weight_factor, 5)

    def test_bulk_create_class_method(self):
        # just run to make sure not raise errors
        old_count = self.wb.webpage.meta_tags.count()
        self.model.bulk_create(
            self.wb.webpage, tags=[
                {'name': 'keywords', 'content': 'one, two, three'},
                {'name': 'name', 'content': 'one, two, three'},
                {'name': 'pla pla pla', 'content': 'one, two, three'},
            ]
        )
        self.assertEqual(self.wb.webpage.meta_tags.count(), old_count + 3)


class WebpageHeaderTestCase(TestCase):
    model = models.WebpageHeader

    def setUp(self) -> None:
        disconnect_signals(self.model)

        wb = BookmarkWebpageTestCase()
        wb.setUp()

        self.wb = wb
        self.text = 'yes, this is meta_tag'
        self.level = 1
        self.obj = self.model.objects.create(
            webpage=wb.webpage, text=self.text, level=self.level)

    def test_save_method(self):
        # is content cleaned
        self.assertIsNotNone(self.obj.cleaned_text)
        self.assertEqual(self.obj.cleaned_text,  'yes meta tag')

    def test_tagname_property(self):
        self.assertEqual(self.obj.tagname, 'h1')

    def test_weight_factor_property(self):
        obj = self.obj
        self.assertEqual(obj.weight_factor, 9)

        obj.level = 6
        self.assertEqual(obj.weight_factor, 1)

    def test_bulk_create_class_method(self):
        # just run to make sure not raise errors
        old_count = self.wb.webpage.headers.count()
        self.model.bulk_create(
            self.wb.webpage, headers=[
                {'h1': ['keywords', 'content', 'one, two, three']},
                {'h2': ['keywords', 'content', 'one, two, three']},
                {'h3': ['keywords', 'content', 'one, two, three']},
            ]
        )
        self.assertEqual(self.wb.webpage.headers.count(), old_count + 9)


class TagTestCase(TestCase):
    model = models.Tag

    def setUp(self) -> None:
        self.user = ObjFactory.create_user()
        self.bookmark = ObjFactory.create_bookmark(
            user=self.user, url='https://google.com')

    def deprecated_test_create_word_reflect_tag(self):
        word, weight1 = 'hello', 10
        word_obj = models.DocumentWordWeight(
            bookmark=self.bookmark, word=word, weight=weight1
        )
        word_obj.save()

        # check tag created with word
        tag = models.Tag.objects.filter(user=self.user, name=word)
        self.assertEqual(tag.count(), 1)
        self.assertEqual(tag[0].weight, weight1)

        # create again and make sure tag merged not duplicated
        word, weight2 = 'hello', 3
        word_obj = models.DocumentWordWeight.objects.create(
            bookmark=self.bookmark, word=word, weight=weight2
        )

        tag = models.Tag.objects.filter(user=self.user, name=word)
        self.assertEqual(tag.count(), 1)
        self.assertEqual(tag[0].weight, weight1 + weight2)

        # check bulk create words reflect tag
        words = [
            {'word': 'fun', 'weight': 10},
            {'word': 'hi', 'weight': 8},
            {'word': 'you', 'weight': 3},
            {'word': 'me', 'weight': 4},
        ]
        words_objs = models.DocumentWordWeight.objects.bulk_create([
            models.DocumentWordWeight(bookmark=self.bookmark, **word)
            for word in words
        ])

        tags = models.Tag.objects.filter(user=self.user, name__in=[
            word_obj.word for word_obj in words_objs
        ])

        self.assertEqual(tags.count(), 4)
        self.assertEqual(
            tags.aggregate(total=Sum('weight'))['total'],
            sum([word_obj.weight for word_obj in words_objs])
        )
