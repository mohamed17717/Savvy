import hashlib

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from common.utils import array_utils, file_utils, math_utils, string_utils


class UtilsTestCase(TestCase):
    def setUp(self) -> None:
        ...

    def test_window_list(self):
        cases = {
            "normal_case_size_2": ([1, 2, 3, 4, 5], 2, [[1, 2], [3, 4], [5]]),
            "normal_case_size_3": ([1, 2, 3, 4, 5], 3, [[1, 2, 3], [4, 5]]),
            "normal_case_size_5": ([1, 2, 3, 4, 5], 5, [[1, 2, 3, 4, 5]]),
            "edge_case_size_1": ([1, 2, 3, 4, 5], 1, [[1], [2], [3], [4], [5]]),
            "edge_case_size_10": ([1, 2, 3, 4, 5], 10, [[1, 2, 3, 4, 5]]),
            "edge_case_empty_list_size_10": ([], 10, [[]]),
        }

        error_cases = {
            "edge_case_size_0": ([1, 2, 3, 4, 5], 0, ZeroDivisionError),
            "edge_case_negative_size": ([1, 2, 3, 4, 5], -1, ZeroDivisionError),
        }

        for name, (data, size, expected) in cases.items():
            with self.subTest(name):
                c = list(array_utils.window_list(data, size))
                self.assertEqual(c, expected)

        for name, (data, size, expected) in error_cases.items():
            with self.subTest(name):
                with self.assertRaises(ZeroDivisionError):
                    list(array_utils.window_list(data, size))

    def test_unique_dicts_in_list(self):
        cases = {
            "normal_case": (
                [{"id": 1}, {"id": 2}, {"id": 1}],
                "id",
                [{"id": 1}, {"id": 2}],
            ),
            "edge_case_empty_data": ([], "id", []),
            "edge_case_missing_key": ([{"id": 1}, {"value": "b"}], "id", [{"id": 1}]),
            "edge_case_single_element": ([{"id": 1}, {"id": 1}], "id", [{"id": 1}]),
            "edge_case_none_value": (
                [{"id": None}, {"id": None}],
                "id",
                [{"id": None}],
            ),
        }

        for name, (data, key, expected) in cases.items():
            with self.subTest(name):
                c = list(array_utils.unique_dicts_in_list(data, key))
                self.assertEqual(c, expected)

    def test_hash_file(self):
        def get_file(data):
            return SimpleUploadedFile("test.txt", data)

        def get_expected_hash(data):
            return hashlib.sha256(data).hexdigest()

        cases = {
            "normal_case": (
                get_file(b"Hello, world!"),
                get_expected_hash(b"Hello, world!"),
            ),
            "edge_case_empty_data": (get_file(b""), get_expected_hash(b"")),
            "edge_case_large_file": (
                get_file(b"a" * 10**6),
                get_expected_hash(b"a" * 10**6),
            ),
        }

        for name, (file_, expected) in cases.items():
            with self.subTest(name):
                c = file_utils.hash_file(file_)
                self.assertEqual(c, expected)

    def test_random_filename(self):
        c = file_utils.random_filename("./")
        self.assertIsInstance(c, str)

    def test_minmax(self):
        cases = {
            "normal_case": (5, 0, 10, 5),
            "normal_case_top": (5, 0, 4, 4),
            "normal_case_bottom": (5, 6, 10, 6),
            "edge_case_equal": (5, 5, 5, 5),
            "edge_case_top": (5, 0, 5, 5),
        }

        error_cases = {
            "edge_case_bottom_bigger": (5, 6, 5, ValueError),
        }

        for name, (num, bottom, top, expected) in cases.items():
            with self.subTest(name):
                c = math_utils.minmax(num, bottom, top)
                self.assertEqual(c, expected)

        for name, (num, bottom, top, expected) in error_cases.items():
            with self.subTest(name):
                with self.assertRaises(ValueError):
                    math_utils.minmax(num, bottom, top)

    def test_random_string(self):
        c = string_utils.random_string(10)
        self.assertIsInstance(c, str)
