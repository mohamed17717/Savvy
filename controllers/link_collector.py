import json

from bs4 import BeautifulSoup
from dataclasses import asdict

from common.utils.dto import Bookmark
from common.utils.files import load_file


class BrowserBookmarkCollector:
    """take browser bookmark html file, parse it and returning list[Bookmark]"""

    def __init__(self, path: str):
        self.path = path
        self.file_content = load_file(path)

    def from_html(self) -> list[Bookmark]:
        soup = BeautifulSoup(self.file_content, 'lxml')

        bookmarks: list[Bookmark] = []

        for item in soup.select('a'):
            attrs = item.attrs.copy()

            attrs['url'] = attrs.pop('href')
            attrs['title'] = item.text

            bookmarks.append(Bookmark.load(attrs))

        return bookmarks

    def from_json(self) -> list[Bookmark]:
        data = json.loads(self.file_content)
        return [Bookmark.load(item) for item in data]

    def to_json(self) -> str:
        bookmarks = tuple(map(asdict, self.from_html()))
        json_bookmarks = json.dumps(bookmarks, indent=2, ensure_ascii=False)

        return json_bookmarks

