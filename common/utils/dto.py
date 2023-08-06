from itertools import count
import urllib.parse

from dataclasses import dataclass, field
from typing import Optional

from .dicts import stringify_dict


@dataclass
class Bookmark:
    url: str
    title: str

    icon: Optional[str] = None
    icon_uri: Optional[str] = None
    add_date: Optional[int] = None
    last_modified: Optional[int] = None

    id: int = field(default_factory=count().__next__)
    domain: str = field(init=False)

    def __post_init__(self):
        self.domain = urllib.parse.urlparse(self.url).netloc


@dataclass
class HTMLMetaTag:
    name: str
    content: str
    simple_name: str = field(init=False)
    is_allowed: bool = field(init=False)

    def __get_simple_name(self) -> str:
        simple_name = self.name

        if ':' in self.name:
            simple_name = self.name.split(':')[1]

        return simple_name

    def __get_is_allowed(self) -> bool:
        return self.simple_name in [
            'name', 'application-name', 'title', 'site_name', 'description',
            'keywords', 'language', 'locale', 'image', 'updated_time',
            'site', 'creator', 'url'
        ]

    def __post_init__(self):
        self.simple_name = self.__get_simple_name()
        self.is_allowed = self.__get_is_allowed()


@dataclass
class BookmarkWebpage:
    id: int
    url: str
    title: str
    meta_tags: list[HTMLMetaTag] = field(default_factory=lambda: [])
    meta_data: str = field(init=False)

    def __get_meta_data(self):
        meta_data = {}

        for meta in self.meta_tags:
            if meta.is_allowed:
                meta_data[meta.simple_name] = meta.content

        return stringify_dict(meta_data)

    def __post_init__(self):
        self.meta_data = self.__get_meta_data()
