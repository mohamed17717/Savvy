import re
import json
import validators

from bs4 import BeautifulSoup
from abc import ABC, abstractmethod

from django.db.models.fields.files import FieldFile
from django.core.exceptions import ValidationError


class BookmarkFileManager(ABC):
    def __init__(self, file_field: FieldFile) -> None:
        super().__init__()

    @abstractmethod
    def validate(self, raise_exception: bool = False) -> bool:
        pass

    @abstractmethod
    def get_links(self) -> list[dict]:
        pass


class BookmarkHTMLFileManager(BookmarkFileManager):
    def __init__(self, file_field: FieldFile):
        self.src = file_field.read().decode('utf8')
        self.soup = None
        self.is_valid = None

    # --getters--
    def __get_soup(self):
        self.soup = self.soup or BeautifulSoup(self.src, 'lxml')
        return self.soup

    def __get_is_valid(self):
        is_valid = self.is_valid

        if is_valid is None:
            raise ValidationError('Validate first before access the data')
        elif is_valid is False:
            raise ValidationError('Invalid data')

        return is_valid

    # --validation--
    def __validate_contain_links(self):
        soup = self.__get_soup()
        contain_links = soup.select_one('a[href]')
        return bool(contain_links)

    def validate(self, raise_exception=False):
        # TODO keep only absolute links -- should have a schema too
        required = [self.__validate_contain_links()]

        self.is_valid = all(required)

        if not self.is_valid and raise_exception:
            raise ValidationError('Not valid html file.')

        return self.is_valid

    # --generate links--
    def __extract(self):
        soup = self.__get_soup()

        links = []
        for item in soup.select('a'):
            attrs = item.attrs.copy()

            attrs['url'] = attrs.pop('href')
            attrs['title'] = item.text

            links.append(attrs)
        return links

    def get_links(self):
        is_valid = self.__get_is_valid()
        if is_valid:
            return self.__extract()


class BookmarkJSONFileManager(BookmarkFileManager):
    def __init__(self, file_field: FieldFile):
        self.data = json.loads(file_field.read().decode('utf8'))
        self.is_valid = None

    # --getters--
    def __get_is_valid(self):
        is_valid = self.is_valid

        if is_valid is None:
            raise ValidationError('Validate first before access the data')
        elif is_valid is False:
            raise ValidationError('Invalid data')

        return is_valid

    # --validation--
    def validate(self, raise_exception=False):
        required = [
            # its an array
            lambda: type(self.data) is list,
            # all items are str
            lambda: all([type(i) is str for i in self.data]),
            # all items are urls
            lambda: all([bool(validators.url(i)) for i in self.data]),
        ]
        # lazy execute
        self.is_valid = all([func() for func in required])

        if not self.is_valid and raise_exception:
            raise ValidationError('Not valid html file.')

        return self.is_valid

    # --generate links--
    def __build_link(self, link):
        """This function make sure output from both get_links are same structure"""
        return {'url': link}

    def get_links(self):
        is_valid = self.__get_is_valid()
        if is_valid:
            links = map(self.__build_link, self.data)
            return list(links)
