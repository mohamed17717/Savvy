
import json
from dataclasses import asdict

from pprint import pprint
from controllers.link_collector import BrowserBookmarkCollector
from controllers.scraper import BrowserBookmarkScraper
from controllers.document_builder import BookmarkDocumentBuilder

from common.utils.files import dump_to_file, load_file
from common.utils.dto import BookmarkWebpage, Bookmark, HTMLMetaTag


def test_collector_from_html():
    collector = BrowserBookmarkCollector(
        'resources/bookmarks/firefox_bookmarks.html')
    bookmarks = collector.from_html()

    pprint(bookmarks)
    return bookmarks


def test_collector_to_json():
    collector = BrowserBookmarkCollector(
        'resources/bookmarks/firefox_bookmarks.html')
    json_bookmarks = collector.to_json()
    dump_to_file('../bookmarks.json', json_bookmarks)
    print('DONE')


def test_scraper():
    bookmarks = test_collector_from_html()
    webpages = []
    for bookmark in bookmarks:
        print(bookmark.url)
        try:
            scraper = BrowserBookmarkScraper(bookmark)
            webpage = scraper.pull()
            webpages.append(asdict(webpage))
        except Exception as e:
            print(e)
        print('--------------------')

    dump_to_file('../bookmarks_webpage.json',
                 json.dumps(webpages, indent=2, ensure_ascii=False))


def test_document_builder():
    bookmarks_data = json.loads(load_file('../bookmarks.json'))
    bookmarks = []
    for item in bookmarks_data:
        item.pop('domain', '')
        bookmarks.append(Bookmark(**item))
    
    
    webpages_data = json.loads(load_file('../bookmarks_webpage.json'))
    webpages = []
    for item in webpages_data:
        item.pop('meta_data')

        meta_tags = []
        for i in item.pop('meta_tags'):
            i.pop('simple_name', '')
            i.pop('is_allowed', '')
            meta_tags.append(
                HTMLMetaTag(**i)
            )
            
        webpages.append(
            BookmarkWebpage(
                meta_tags=meta_tags,
                **item,
            )
        )

    for bookmark, webpage in zip(bookmarks, webpages):
        builder = BookmarkDocumentBuilder(bookmark, webpage)
        print(builder.build())
        print('----------------')
