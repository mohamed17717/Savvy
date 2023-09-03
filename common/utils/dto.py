from itertools import count
import urllib.parse

from dataclasses import dataclass, field
from typing import Optional

from .dicts import stringify_dict


@dataclass
class Bookmark:
    url: str
    title: str

    # OPTIONAL
    icon: Optional[str] = None
    icon_uri: Optional[str] = None
    add_date: Optional[int] = None
    last_modified: Optional[int] = None

    # COMPUTED
    id: int = field(default_factory=count().__next__)
    domain: str = field(init=False)

    # TODO add BookmarkWebpage on this class

    def __get_domain(self) -> str:
        return urllib.parse.urlparse(self.url).netloc

    def __post_init__(self):
        self.domain = self.__get_domain()

    @classmethod
    def load(cls, data: dict) -> 'Bookmark':
        return cls(
            url=data.get('url'),
            title=data.get('title'),
            icon=data.get('icon'),
            icon_uri=data.get('icon_uri'),
            add_date=data.get('add_date'),
            last_modified=data.get('last_modified'),
        )


@dataclass
class HTMLMetaTag:
    name: str
    content: str

    # COMPUTED
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

    @classmethod
    def load(cls, data: dict) -> 'HTMLMetaTag':
        return cls(
            name=data.get('name'),
            content=data.get('content'),
        )


@dataclass
class BookmarkWebpage:
    id: int
    url: str
    title: str

    # OPTIONAL
    # TODO Check why it become null in some values
    meta_tags: Optional[list[HTMLMetaTag]] = field(default_factory=lambda: [])

    # COMPUTED
    meta_data: str = field(init=False)

    def __get_meta_data(self):
        # meta_data = {}
        # if self.meta_tags:
        #     for meta in self.meta_tags:
        #         if meta.is_allowed:
        #             meta_data[meta.simple_name] = meta.content

        # return stringify_dict(meta_data)
        
        meta_data = ''
        if self.meta_tags:
            for meta in self.meta_tags:
                if meta.is_allowed:
                    meta_data += ' ' + meta.content

        return meta_data

    def __post_init__(self):
        self.meta_data = self.__get_meta_data()

    @classmethod
    def load(cls, data: dict) -> 'BookmarkWebpage':
        return cls(
            id=data.get('id'),
            url=data.get('url'),
            title=data.get('title'),
            meta_tags=data.get('meta_tags'),
        )
