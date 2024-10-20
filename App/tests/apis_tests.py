import json
import os
from time import sleep

from celery.result import AsyncResult
from django.urls import reverse
from knox.models import AuthToken
from rest_framework import status
from rest_framework.test import APITestCase

from App import models
from App.tests.models_tests import ObjFactory, disconnect_signals


def knox_authorize(user, test_case):
    token = AuthToken.objects.create(user)[1]
    test_case.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")


class BookmarkFileAPITestCase(APITestCase):
    model = models.BookmarkFile

    def setUp(self) -> None:
        user = ObjFactory.create_user(username="mhameho")
        knox_authorize(user, self)

        self.reconnect_signals = disconnect_signals(self.model)

        self.user = user
        self.file = ObjFactory.create_dummy_bookmark_file(user)

    def tearDown(self) -> None:
        self.reconnect_signals()

    def test_file_read(self):
        endpoint = reverse("app:file-detail", args=(self.file.pk,))
        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_file_read_unowned_file(self):
        other_user = ObjFactory.create_user(username="the_other")
        other_file = ObjFactory.create_dummy_bookmark_file(other_user)

        endpoint = reverse("app:file-detail", args=(other_file.pk,))
        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_file_delete(self):
        dummy_file = ObjFactory.create_dummy_bookmark_file(self.user)
        endpoint = reverse("app:file-detail", args=(dummy_file.pk,))
        response = self.client.delete(endpoint)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_file_list(self):
        endpoint = reverse("app:file-list")
        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class BookmarkFileUploadAPITestCase(APITestCase):
    model = models.BookmarkFile

    def setUp(self) -> None:
        user = ObjFactory.create_user(username="mhameho")
        knox_authorize(user, self)

        self.user = user

    def test_file_create(self):
        # Create test file in location
        urls = [
            "https://dev.to/koladev/authentication-in-tests-with-drf-4jin",
            # 'https://dev.to/devteam/what-was-your-win-this-week-30k1',
            # 'https://dev.to/devteam/dev-community-contributor-spotlight-christine-belzie-38bg',
            # 'https://dev.to/lucamartial/why-is-it-so-important-to-evaluate-large-language-models-llms-59jl',
            # 'https://dev.to/encore/building-a-fully-type-safe-event-driven-backend-in-go-2g8m',
        ]
        file_path = "./test_file.json"
        with open(file_path, "w") as f:
            f.write(json.dumps(urls, ensure_ascii=False))

        # POST file to the endpoint
        endpoint = reverse("app:file-create")
        data = {"location": open(file_path, "rb")}
        response = self.client.post(endpoint, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # get the file object
        response_data = response.json()
        bookmark_file = self.user.bookmark_files.get(pk=response_data["id"])

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
        # task_id = bookmark_file.tasks[-1]
        # task = AsyncResult(task_id)
        # self.assertNotEqual(task.state.lower(), 'pending')

        # NOTE celery runs eager mode so can't run 2 tasks simultaneously
        # wait until the task is done or 2s for each link
        # WAIT = 2  # seconds
        # MAX_TRIES = len(urls) or 1
        # try_number = 0
        # task_status = False
        # while try_number < (MAX_TRIES+10):
        #     try_number += 1
        #     sleep(WAIT)

        #     task = AsyncResult(task_id)
        #     if task.state.upper() == 'SUCCESS':
        #         task_status = True
        #         break

        # self.assertTrue(task_status)  # if task can't be failed

        # scrapy will be have its own test

        # delete file from location
        os.remove(file_path)


class BookmarkAPITestCase(APITestCase):
    model = models.Bookmark

    def setUp(self) -> None:
        user = ObjFactory.create_user(username="mhameho")
        knox_authorize(user, self)

        self.reconnect_signals = disconnect_signals(self.model)

        self.user = user
        self.bookmark = ObjFactory.create_bookmark(user, url="https://google.com")

    def tearDown(self) -> None:
        self.reconnect_signals()

    def test_bookmark_read(self):
        endpoint = reverse("app:bookmark-detail", args=(self.bookmark.pk,))
        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_bookmark_read_unowned_file(self):
        other_user = ObjFactory.create_user(username="the_other")
        other_bookmark = ObjFactory.create_bookmark(
            other_user, url="https://google.com"
        )

        endpoint = reverse("app:bookmark-detail", args=(other_bookmark.pk,))
        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_bookmark_list(self):
        endpoint = reverse("app:bookmark-list")
        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ClusterAPITestCase(APITestCase):
    model = models.Cluster

    def setUp(self) -> None:
        user = ObjFactory.create_user(username="mhameho")
        knox_authorize(user, self)

        self.reconnect_signals = disconnect_signals(self.model)

        self.user = user
        self.cluster = ObjFactory.create_cluster(user)

    def tearDown(self) -> None:
        self.reconnect_signals()

    def test_cluster_read(self):
        endpoint = reverse("app:cluster_read-detail", args=(self.cluster.pk,))
        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cluster_read_unowned_file(self):
        other_user = ObjFactory.create_user(username="the_other")
        other_cluster = ObjFactory.create_cluster(other_user)

        endpoint = reverse("app:cluster_read-detail", args=(other_cluster.pk,))
        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cluster_list(self):
        endpoint = reverse("app:cluster_read-list")
        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TagsMostWeightedListAPITestCase(APITestCase):
    model = models.Tag

    def setUp(self) -> None:
        user = ObjFactory.create_user(username="mhameho")
        knox_authorize(user, self)

        self.user = user
        self.bookmark = ObjFactory.create_bookmark(user, url="https://google.com")
        self.tag = models.Tag.objects.create(user=self.user, name="hello")
        self.tag.bookmarks.add(self.bookmark)

    def test_tag_read(self):
        endpoint = reverse("app:tag_read-detail", args=(self.tag.pk,))
        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_tag_list(self):
        endpoint = reverse("app:tag_read-list")
        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_tag_list_unowned_tag(self):
        other_user = ObjFactory.create_user(username="the_other")
        other_bookmark = ObjFactory.create_bookmark(
            other_user, url="https://google.com"
        )
        other_tag = models.Tag.objects.create(user=other_user, name="hello")
        other_tag.bookmarks.add(other_bookmark)

        endpoint = reverse("app:tag_read-detail", args=(other_tag.pk,))
        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_tag_most_weighted_list(self):
        endpoint = reverse("app:tag_most_weighted")
        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
