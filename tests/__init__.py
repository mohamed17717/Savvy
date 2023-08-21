
import json
from dataclasses import asdict

from pprint import pprint
from controllers.link_collector import BrowserBookmarkCollector
from controllers.scraper import BrowserBookmarkScraper
from controllers.document_builder import BookmarkDocumentBuilder, BookmarkWeightedDocumentBuilder

from common.utils.files import dump_to_file, load_file
from common.utils.dto import BookmarkWebpage, Bookmark, HTMLMetaTag
from common.utils.string import clean_text


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
        bookmarks.append(Bookmark.load(item))

    webpages_data = json.loads(load_file('../bookmarks_webpage.json'))
    webpages = []
    for item in webpages_data:
        item.setdefault('meta_tags', [])

        meta_tags = []
        for i in item.pop('meta_tags') or []:
            meta_tags.append(HTMLMetaTag.load(i))

        item['meta_tags'] = meta_tags
        webpages.append(BookmarkWebpage.load(item))

    if len(bookmarks) != len(webpages):
        raise Exception('invalid bookmarks, webpages data')

    for bookmark, webpage in zip(bookmarks, webpages):
        # builder = BookmarkDocumentBuilder(bookmark, webpage)
        builder = BookmarkWeightedDocumentBuilder(bookmark, webpage)
        document = json.dumps(builder.build(), ensure_ascii=False, indent=2)
        dump_to_file(f'resources/documents/{webpage.id+1}+.json', document)
        print(document)
        print('----------------')


def test_clean_documents():
    files = [f'resources/documents/{i}.txt' for i in range(1, 20)]
    docs = map(load_file, files)
    
    for path, doc in zip(files, docs):
        dump_to_file(f'{path}.cleaned', clean_text(doc))
        