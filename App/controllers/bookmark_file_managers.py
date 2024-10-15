import json
import re
from abc import ABC, abstractmethod

import validators
from bs4 import BeautifulSoup
from django.core.exceptions import ValidationError
from django.db.models.fields.files import FieldFile


class BookmarkFileManager(ABC):
    def __init__(self, file_field: FieldFile) -> None:
        super().__init__()

    @property
    def is_valid(self):
        if self._is_valid is None:
            raise ValidationError("Validate first before access the data")
        elif self._is_valid is False:
            raise ValidationError("Invalid data")

        return self._is_valid

    @abstractmethod
    def validate(self) -> bool:
        pass

    @abstractmethod
    def get_links(self) -> list[dict]:
        pass


class BookmarkHTMLFileManager(BookmarkFileManager):
    def __init__(self, file_field: FieldFile):
        self.file = file_field

        self._is_valid = None
        self._soup = None

    @property
    def soup(self):
        self.file.seek(0)
        self._soup = self._soup or BeautifulSoup(self.get_src(), "lxml")
        return self._soup

    def get_src(self, length: int = None):
        self.file.seek(0)
        content = self.file.read(length)
        return content.decode("utf8")

    def validate(self):
        def contain_links():
            regex = r"<a\s+?href=[\"\']http[s]{0,1}://.+?[\"\']"
            regex = re.compile(regex, re.IGNORECASE)
            match = re.search(regex, self.get_src(3000))
            return bool(match)

        checks = [contain_links]
        if self._is_valid is None:
            self._is_valid = all([check() for check in checks])

        return self.is_valid

    def get_links(self):
        self.validate()

        links = []
        for item in self.soup.select("a"):
            attrs = item.attrs.copy()

            attrs["url"] = attrs.pop("href")
            attrs["title"] = item.text
            attrs["added_at"] = attrs.pop("add_date", None)

            links.append(attrs)
        return links


class BookmarkJSONFileManager(BookmarkFileManager):
    def __init__(self, file_field: FieldFile):
        self.data = json.loads(file_field.read().decode("utf8"))
        self._is_valid = None

    def validate(self):
        def data_is_list():
            return isinstance(self.data, list)

        def items_are_str():
            return all([isinstance(i, str) for i in self.data])

        def items_are_links():
            return all([bool(validators.url(i)) for i in self.data])

        checks = [data_is_list, items_are_str, items_are_links]
        if self._is_valid is None:
            self._is_valid = all([check() for check in checks])

        return self.is_valid

    def get_links(self):
        self.validate()
        return [{"url": url} for url in self.data]
