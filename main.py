import os

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
    for bookmark in bookmarks:
        try:
            scraper = BrowserBookmarkScraper(bookmark)
            scraper.pull()
        except Exception as e:
            print(e)
        print('--------------------')
    
    # json_bookmarks = collector.to_json(bookmarks)
    # dump_to_file('../bookmarks.json', json_bookmarks)


if __name__ == '__main__':
    main()