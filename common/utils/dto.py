
from dataclasses import dataclass
from typing import Optional


@dataclass
class Bookmark:
    url: str
    title: str

    icon: Optional[str] = None
    icon_uri: Optional[str] = None
    add_date: Optional[int] = None
    last_modified: Optional[int] = None
