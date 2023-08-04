import json

from bs4 import BeautifulSoup
from dataclasses import asdict

from common.utils.dto import Bookmark
from common.utils.files import load_file


class BrowserBookmark:
    """take browser bookmark html file, parse it and returning list[Bookmark]"""

    def __init__(self, path: str):
        self.path = path

    def parse(self) -> list[Bookmark]:
        html = load_file(self.path)
        soup = BeautifulSoup(html, 'lxml')

        bookmarks: list[Bookmark] = []

        for item in soup.select('a'):
            attrs = item.attrs.copy()

            attrs['url'] = attrs.pop('href')
            attrs['title'] = item.text

            bookmarks.append(Bookmark(**attrs))

        return bookmarks

    def to_json(self) -> str:
        bookmarks = tuple(map(asdict, self.parse()))
        json_bookmarks = json.dumps(bookmarks, indent=2, ensure_ascii=False)

        return json_bookmarks
