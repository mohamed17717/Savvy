import requests
from bs4 import BeautifulSoup

from common.utils.dto import Bookmark, BookmarkWebpage, HTMLMetaTag
from common.utils.dicts import get_by_alias


class BrowserBookmarkScraper:
    def __init__(self, bookmark: Bookmark):
        self.bookmark = bookmark

    def pull(self):
        print(f'[pull] {self.bookmark.url}')
        res = requests.get(self.bookmark.url, timeout=3)
        assert res.status_code == 200, f'Error request [{res.status_code}]'

        soup = BeautifulSoup(res.text, 'lxml')

        webpage = BookmarkWebpage(
            id=self.bookmark.id,
            url=self.bookmark.url,
            title=soup.select_one('title').text
        )
        meta_tags = []
        for elm in soup.select('meta[content]'):
            name = get_by_alias(
                elm.attrs, ['name', 'property', 'itemprop'], 'undefined')
            meta_tag = HTMLMetaTag(
                name=name,
                content=elm.attrs.get('content')
            )
            meta_tags.append(meta_tag)

        webpage.meta_tags = meta_tags
        return webpage
