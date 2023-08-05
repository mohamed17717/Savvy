import os
import json
from dataclasses import asdict

from pprint import pprint
from controllers.link_collector import BrowserBookmarkCollector
from controllers.scraper import BrowserBookmarkScraper

from common.utils.files import dump_to_file



def main():
    # make sure that iam in base dir `src`
    if os.getcwd().endswith('src') is False:
        os.chdir('./src')

    collector = BrowserBookmarkCollector('resources/bookmarks/firefox_bookmarks.html')
    bookmarks = collector.from_html()
    web_pages = []
    for bookmark in bookmarks:
        print(bookmark.url)
        try:
            scraper = BrowserBookmarkScraper(bookmark)
            web_page = scraper.pull()
            web_pages.append(asdict(web_page))
        except Exception as e:
            print(e)
        print('--------------------')
    
    # json_bookmarks = collector.to_json(bookmarks)
    dump_to_file('../bookmarks_webpage.json',
                 json.dumps(web_pages, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()