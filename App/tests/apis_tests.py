import json
import os
from time import sleep

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from knox.models import AuthToken
from celery.result import AsyncResult

from App import models
from App.tests.models_tests import ObjFactory, disconnect_signals


def knox_authorize(user, test_case):
    token = AuthToken.objects.create(user)[1]
    test_case.client.credentials(HTTP_AUTHORIZATION='Token ' + token)


class BookmarkFileAPITestCase(APITestCase):
    model = models.BookmarkFile

    def setUp(self) -> None:
        user = ObjFactory.create_user(username='mhameho')
        knox_authorize(user, self)

        disconnect_signals(self.model)

        self.user = user
        self.file = ObjFactory.create_dummy_bookmark_file(user)

    def test_file_read(self):
        endpoint = reverse('app:file-detail', args=(self.file.pk,))
        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_file_read_unowned_file(self):
        other_user = ObjFactory.create_user(username='the_other')
        other_file = ObjFactory.create_dummy_bookmark_file(other_user)

        endpoint = reverse('app:file-detail', args=(other_file.pk,))
        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_file_delete(self):
        dummy_file = ObjFactory.create_dummy_bookmark_file(self.user)
        endpoint = reverse('app:file-detail', args=(dummy_file.pk,))
        response = self.client.delete(endpoint)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_file_list(self):
        endpoint = reverse('app:file-list')
        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class BookmarkFileUploadAPITestCase(APITestCase):
    model = models.BookmarkFile

    def setUp(self) -> None:
        user = ObjFactory.create_user(username='mhameho')
        knox_authorize(user, self)

        self.user = user

    def test_file_create(self):
        # Create test file in location
        urls = [
            'https://dev.to/koladev/authentication-in-tests-with-drf-4jin',
            'https://dev.to/devteam/what-was-your-win-this-week-30k1',
            'https://dev.to/devteam/dev-community-contributor-spotlight-christine-belzie-38bg',
            'https://dev.to/lucamartial/why-is-it-so-important-to-evaluate-large-language-models-llms-59jl',
            'https://dev.to/encore/building-a-fully-type-safe-event-driven-backend-in-go-2g8m',
        ]
        file_path = './test_file.json'
        with open(file_path, 'w') as f:
            f.write(json.dumps(urls, ensure_ascii=False))

        # POST file to the endpoint
        endpoint = reverse('app:file-create')
        data = {
            'location': open(file_path, 'rb')
        }
        response = self.client.post(endpoint, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # get the file object
        response_data = response.json()
        bookmark_file = self.user.bookmark_files.get(pk=response_data['id'])

        # make sure file created and contain 5 urls
        self.assertEqual(len(bookmark_file.bookmarks_links), len(urls))

        #####
        # After view is done and return response i expect 2 things
        # 1- bookmarks are created
        # 2- task for crawling is created
        #####

        # make sure bookmarks created
        self.assertEqual(bookmark_file.bookmarks.count(), len(urls))

        # make sure crawling task created
        self.assertGreaterEqual(len(bookmark_file.tasks), 1)
        task_id = bookmark_file.tasks[-1]
        task = AsyncResult(task_id)
        self.assertNotEqual(task.state.lower(), 'pending')

        # wait until the task is done or 2s for each link
        WAIT = 2  # seconds
        MAX_TRIES = len(urls) or 1
        try_number = 0
        task_status = False
        while try_number < MAX_TRIES:
            task = AsyncResult(task_id)
            print(f'{task_id=}, {task.state=}, ({try_number=}), {MAX_TRIES=}')
            if task.state.upper() == 'SUCCESS':
                task_status = True
                break
            try_number += 1
            sleep(WAIT)

        self.assertTrue(task_status)  # if task can't be failed

        # bookmark crawled status is changes
        # self.assertGreaterEqual(
        #     bookmark_file.bookmarks.filter(crawled=True).count(), 1
        # )

        # scrapy log created
        scrapes = models.ScrapyResponseLog.objects.filter(
            bookmark__in=bookmark_file.bookmarks.all())
        self.assertGreaterEqual(scrapes.count(), len(urls))

        # bookmarks webpage header and meta created
        webpages = models.BookmarkWebpage.objects.filter(
            bookmark__in=bookmark_file.bookmarks.all())
        self.assertGreaterEqual(webpages.count(), len(urls))

        meta_tags = models.WebpageMetaTag.objects.filter(webpage__in=webpages)
        self.assertGreaterEqual(meta_tags.count(), len(urls))

        headers = models.WebpageHeader.objects.filter(webpage__in=webpages)
        self.assertGreaterEqual(headers.count(), len(urls))

        # bookmarks have word vector
        words = models.DocumentWordWeight.objects.filter(
            bookmark__in=bookmark_file.bookmarks.all())
        self.assertGreaterEqual(words.count(), len(urls))

        # bookmarks got clustered
        clusters = models.DocumentCluster.objects.filter(
            bookmarks__in=bookmark_file.bookmarks.all())
        self.assertGreaterEqual(clusters.count(), 1)

        # clustered got labels
        cluster_labels = models.ClusterTag.objects.filter(cluster__in=clusters)
        self.assertGreaterEqual(cluster_labels.count(), 1)

        # delete file from location
        os.remove(file_path)


class BookmarkAPITestCase(APITestCase):
    model = models.Bookmark

    def setUp(self) -> None:
        user = ObjFactory.create_user(username='mhameho')
        knox_authorize(user, self)

        disconnect_signals(self.model)

        self.user = user
        self.bookmark = ObjFactory.create_bookmark(
            user, url='https://google.com')

    def test_bookmark_read(self):
        endpoint = reverse('app:bookmark-detail', args=(self.bookmark.pk,))
        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_bookmark_read_unowned_file(self):
        other_user = ObjFactory.create_user(username='the_other')
        other_bookmark = ObjFactory.create_bookmark(
            other_user, url='https://google.com')

        endpoint = reverse('app:bookmark-detail', args=(other_bookmark.pk,))
        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_bookmark_list(self):
        endpoint = reverse('app:bookmark-list')
        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ClusterAPITestCase(APITestCase):
    model = models.DocumentCluster

    def setUp(self) -> None:
        user = ObjFactory.create_user(username='mhameho')
        knox_authorize(user, self)

        disconnect_signals(self.model)

        self.user = user
        self.cluster = ObjFactory.create_cluster(user)

    def test_cluster_read(self):
        endpoint = reverse('app:cluster_read-detail', args=(self.cluster.pk,))
        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cluster_read_unowned_file(self):
        other_user = ObjFactory.create_user(username='the_other')
        other_cluster = ObjFactory.create_cluster(other_user)

        endpoint = reverse('app:cluster_read-detail', args=(other_cluster.pk,))
        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cluster_list(self):
        endpoint = reverse('app:cluster_read-list')
        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
