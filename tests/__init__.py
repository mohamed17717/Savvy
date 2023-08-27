
import os
import json
from dataclasses import asdict

from pprint import pprint
from controllers.link_collector import BrowserBookmarkCollector
from controllers.scraper import BrowserBookmarkScraper
from controllers.document_builder import BookmarkDocumentBuilder, BookmarkWeightedDocumentBuilder
from controllers.document_cluster import CosineSimilarityCluster
from controllers.labelling import ClusterLabelBuilder

from common.utils.files import dump_to_file, load_file
from common.utils.dto import BookmarkWebpage, Bookmark, HTMLMetaTag
from common.utils.string import clean_string


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
        dump_to_file(
            f'resources/results/document-builder/<5-test>/{webpage.id+1}.json', document)
        print(document)
        print('----------------')


def test_clean_documents():
    files = [
        f'resources/results/document-builder/1-text/{i}.txt' for i in range(1, 20)]
    docs = map(load_file, files)

    for path, doc in zip(files, docs):
        dump_to_file(f'{path}.cleaned', clean_string(doc))


def test_cluster_documents():
    def get_paths() -> list[str]:
        DIR = './resources/results/document-builder/4-weighted-json-cleaned/'

        def fname(i): return int(
            i.split('/')[-1].split('.')[0].strip('+'))  # get filename

        files = os.listdir(DIR)
        files = filter(lambda f: f.endswith('.json'), files)
        files = map(lambda f: DIR + f, files)
        files = list(files)
        files = sorted(files, key=fname)

        return files

    files = get_paths()

    documents = map(load_file, files)
    documents = map(json.loads, documents)
    documents = tuple(documents)

    cosine_sim = CosineSimilarityCluster(documents)

    clusters = cosine_sim.get_clusters(0.4)

    # translate indexes to names
    t_clusters = []
    for cluster in clusters:
        t_cluster = []
        for index in cluster:
            t_cluster.append(files[index])
        t_clusters.append(t_cluster)

    print(clusters)
    print(json.dumps(t_clusters, indent=2))


def test_label_clusters():
    clusters_paths = load_file('resources/results/cluster/1.json')
    clusters_paths = json.loads(clusters_paths)

    load_cluster_paths = lambda cluster_paths: [json.loads(load_file(path)) for path in cluster_paths]

    clusters = map(load_cluster_paths, clusters_paths)
    clusters = tuple(clusters)

    clusters = map(lambda c: ClusterLabelBuilder(c).build(), clusters)

    for paths, cluster in zip(clusters_paths, clusters):
        if len(paths) == 1: continue
        print(paths)
        print()
        print(cluster)
        print('---------------')

