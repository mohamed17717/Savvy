import sys
import unittest
import json
from unittest import TestCase

from django.core.management import call_command
from django.contrib.auth import get_user_model

from App import models
from .models_tests import ObjFactory


current_file_name = 'App.tests.' + __file__.split('/')[-1].replace('.py', '')
should_skip = current_file_name not in sys.argv

@unittest.skipIf(should_skip, "This test is skipped because the file is not called explicitly in sys.argv")
class BookmarkSpiderTestCase(TestCase):
    def setUp(self) -> None:
        self.urls = [
            'https://dev.to/koladev/authentication-in-tests-with-drf-4jin',
            # 'https://dev.to/devteam/what-was-your-win-this-week-30k1',
            # 'https://dev.to/devteam/dev-community-contributor-spotlight-christine-belzie-38bg',
            # 'https://dev.to/lucamartial/why-is-it-so-important-to-evaluate-large-language-models-llms-59jl',
            # 'https://dev.to/encore/building-a-fully-type-safe-event-driven-backend-in-go-2g8m',
        ]
        self.user = ObjFactory.create_user('hello_scrapy')
        self.bookmarks = []

        for url in self.urls:
            bm = models.Bookmark.objects.create(url=url, user=self.user)
            self.bookmarks.append(bm)

    def test_run_crawl_command(self):
        ids = [bm.id for bm in self.bookmarks]
        call_command('crawl_bookmarks', json.dumps(ids))
        
        # scrapy log created
        scrapes = models.ScrapyResponseLog.objects.filter(bookmark__in=self.bookmarks)
        self.assertGreaterEqual(scrapes.count(), len(self.urls))

        # bookmark crawled status is changes
        bookmarks = models.Bookmark.objects.filter(id__in=ids, crawled=True)
        self.assertGreaterEqual(bookmarks.count(), 1)

        # bookmarks webpage header and meta created
        webpages = models.BookmarkWebpage.objects.filter(bookmark__in=self.bookmarks)
        self.assertGreaterEqual(webpages.count(), len(self.urls))

        meta_tags = models.WebpageMetaTag.objects.filter(webpage__in=webpages)
        self.assertGreaterEqual(meta_tags.count(), len(self.urls))

        headers = models.WebpageHeader.objects.filter(webpage__in=webpages)
        self.assertGreaterEqual(headers.count(), len(self.urls))

        # bookmarks have word vector
        words = models.DocumentWordWeight.objects.filter(bookmark__in=self.bookmarks)
        self.assertGreaterEqual(words.count(), len(self.urls))

        # bookmarks got clustered
        clusters = models.DocumentCluster.objects.filter(bookmarks__in=self.bookmarks)
        self.assertGreaterEqual(clusters.count(), 1)

    def tearDown(self) -> None:
        ids = [bm.id for bm in self.bookmarks]
        models.Bookmark.objects.filter(user=self.user, id__in=ids).delete()
        get_user_model().objects.filter(id=self.user.id).delete()