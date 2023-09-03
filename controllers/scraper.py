import requests
from bs4 import BeautifulSoup

from common.utils.dto import Bookmark, BookmarkWebpage, HTMLMetaTag
from common.utils.dicts import get_by_alias


class BrowserBookmarkScraper:
    def __init__(self, bookmark: Bookmark):
        self.bookmark = bookmark

    def __load_meta_tags(self, soup: BeautifulSoup) -> list[HTMLMetaTag]:
        meta_tags = []

        # TODO make HTMLMetaTag take the html meta as a variable and extract data from it
        for elm in soup.select('meta[content]'):
            data = elm.attrs.copy()
            data['name'] = get_by_alias(
                data, ['name', 'property', 'itemprop'], 'undefined'
            )

            meta_tags.append(HTMLMetaTag.load(data))

        return meta_tags

    def pull(self):
        print(f'[pull] {self.bookmark.url}')
        res = requests.get(self.bookmark.url, timeout=3)

        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'lxml')
            page_data = {
                'id': self.bookmark.id,
                'url': self.bookmark.url,
                'title': soup.select_one('title').text,
                'meta_tags': self.__load_meta_tags(soup)
            }
        else:
            page_data = {
                'id': self.bookmark.id,
                'url': self.bookmark.url,
                'title': f'Error request [{res.status_code}]',
            }

        return BookmarkWebpage.load(page_data)
