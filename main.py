import os
import json
from dataclasses import asdict

from pprint import pprint
from controllers.link_collector import BrowserBookmarkCollector
from controllers.scraper import BrowserBookmarkScraper
from controllers.document_builder import BookmarkDocumentBuilder

from common.utils.files import dump_to_file, load_file
from common.utils.dto import BookmarkWebpage, Bookmark, HTMLMetaTag



def main():
    # make sure that iam in base dir `src`
    if os.getcwd().endswith('src') is False:
        os.chdir('./src')

    bookmarks = json.loads(load_file('../bookmarks.json'))
    bookmarks = [Bookmark(**item) for item in bookmarks]
    webpages = json.loads(load_file('../bookmarks_webpage.json'))
    webpages = [
        BookmarkWebpage(
            meta_tags=[HTMLMetaTag(**i) for i in item.pop('meta_tags')],
            **item,
        ) for item in webpages
    ]
    
    for bookmark, webpage in zip(bookmarks, webpages):
        builder = BookmarkDocumentBuilder(bookmark, webpage)
        print(builder.build())
        print('----------------')
    

    # print(len(bookmarks))
    # print(len(webpages))

    # collector = BrowserBookmarkCollector('resources/bookmarks/firefox_bookmarks.html')
    # bookmarks = collector.from_html()
    # webpages = []
    # for bookmark in bookmarks:
    #     print(bookmark.url)
    #     try:
    #         scraper = BrowserBookmarkScraper(bookmark)
    #         webpage = scraper.pull()
    #         webpages.append(asdict(webpage))
    #     except Exception as e:
    #         print(e)
    #     print('--------------------')
    
    # json_bookmarks = collector.to_json(bookmarks)
    # dump_to_file('../bookmarks_webpage.json',
    #              json.dumps(webpages, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()