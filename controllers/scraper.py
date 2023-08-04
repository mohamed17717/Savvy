import requests
from bs4 import BeautifulSoup

from common.utils.dto import Bookmark


class BrowserBookmarkScraper:
    def __init__(self, bookmark: Bookmark):
        self.bookmark = bookmark

    def pull(self):
        print(f'[pull] {self.bookmark.url}')
        res = requests.get(self.bookmark.url)
        assert res.status_code == 200, f'Error request [{res.status_code}]'

        soup = BeautifulSoup(res.text, 'lxml')
        meta_tags = soup.select('meta')
        for meta in meta_tags:
            print(meta)
