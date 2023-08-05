from itertools import count

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Bookmark:
    url: str
    title: str

    icon: Optional[str] = None
    icon_uri: Optional[str] = None
    add_date: Optional[int] = None
    last_modified: Optional[int] = None

    id: int = field(default_factory=count().__next__)


@dataclass
class HTMLMetaTag:
    name: str
    content: str
    # property // itemprop //


@dataclass
class BookmarkWebPage:
    id: int
    url: str
    title: str
    meta_tags: list[HTMLMetaTag] = field(default_factory=lambda: [])
