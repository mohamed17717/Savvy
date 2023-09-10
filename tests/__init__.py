
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

    def load_cluster_paths(cluster_paths): return [
        json.loads(load_file(path)) for path in cluster_paths]

    clusters = map(load_cluster_paths, clusters_paths)
    clusters = tuple(clusters)

    clusters = map(lambda c: ClusterLabelBuilder(c).build(), clusters)

    for paths, cluster in zip(clusters_paths, clusters):
        if len(paths) == 1:
            continue
        print(paths)
        print()
        print(cluster)
        print('---------------')


def test_text_cleaner():
    from controllers.text_cleaner import TextCleaner
    result = TextCleaner(
        '<span href="https://google.com">Mo Salah is a famous egyptian, &copy; who playing football'
        ' in liverpool with_number 11 and he l//**-oves @shakira website is a  a www.xnxxx.com</span>'
        '\n\n\n\n#never_walk_alone salah@yahoo.com\n\n\n\n'
    ).full_clean().text

    print(result)


def test_bookmark_weight_sheet():
    from controllers.text_cleaner import BookmarkWeightsSheet

    bookmark = Bookmark(
        **{
            "url": "https://www.kali.org/",
            "title": "Kali Linux",
            "icon": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAACbklEQVRYhcXXS4jNYRjH8c8MMyzcxUZZyEaRe1gSohDJuIQsNE1NSSxcCrNBIlbKgoXNoJGNhUSJ3MslYWEiuUXKNSczxrB43zP/v3HOzJzhnPnV2zn/8/8/z/M97/O+z/P+4T6a8QEvcRX12IH5GKbI2o9GtOBXnnEPuzED5cUC6YsJWBmDXcDXHDBPMb0YAH0iwArU4QCO4Qret4Oo/Z+BN+CJjlPQfmzN4WcIFqFXoQD1aMUb3EQDDmInNgrpuObPdJzN4Wd1vHcNowuFqEx9L8dsHMYLuWfgJ1a181EWoVvxWdhBBWkQtuFZjoA/8BgncTf1+6MIWotpEX45MkJK13Y1+PpInXX8EWei48nCDhED1OcAzI63OIJqIWUtqOoKwMVIfRILUJHnuePtAmaEtZPxd4ruxM8MpnYGUClsw460NBXgBRaid7xXLtSGo3LXjtcY2BlEZ3ocnTVhbAfPDUCNULDSENv/JfiIlKMTXbSpEP551u4bhnYXYGbK0ZYC7GbhYcr2llAvCtbUlJO9BdqWCbusCd+FbVtwtewvWelPJIuvEC3BvG7YtalBMguHugnxTxrlz2LVGEE2CC18LqZgpCKeGRYLeeysW37DdewSSnTZ/4QYj/NC0+lq+36AdfJX2G5pOOZgDTZhD07hUwcg94VDT1HVB5vxJQ9Es1DWi65xeCVp5/sk5blJOHMUXWMkKbktlOLL8fq5pM0XVVWS6V+GfpLGVl0KAMIZMjsLhIXYihulApgkmYXsLjgtFLaS6VwEqIvXgzGxlACzIsClUgZNqxfeCW9ZPaYzwiwM6CmAGuG9o60n/AaaQPLjXpBeAAAAAABJRU5ErkJggg==",
            "icon_uri": "https://www.kali.org/images/favicon.ico",
            "add_date": "1653747378",
            "last_modified": "1653747378",
        }
    )
    webpage = BookmarkWebpage(
        **{
            "id": 0,
            "url": "https://www.kali.org/",
            "title": "Kali Linux | Penetration Testing and Ethical Hacking Linux Distribution",
            "meta_tags": [
                {
                    "name": "viewport",
                    "content": "width=device-width",
                    "simple_name": "viewport",
                    "is_allowed": False
                },
                {
                    "name": "name",
                    "content": "Kali Linux | Penetration Testing and Ethical Hacking Linux Distribution",
                    "simple_name": "name",
                    "is_allowed": True
                },
                {
                    "name": "application-name",
                    "content": "Kali Linux | Penetration Testing and Ethical Hacking Linux Distribution",
                    "simple_name": "application-name",
                    "is_allowed": True
                },
                {
                    "name": "twitter:title",
                    "content": "Kali Linux | Penetration Testing and Ethical Hacking Linux Distribution",
                    "simple_name": "title",
                    "is_allowed": True
                },
                {
                    "name": "og:site_name",
                    "content": "Kali Linux",
                    "simple_name": "site_name",
                    "is_allowed": True
                },
                {
                    "name": "og:title",
                    "content": "Kali Linux | Penetration Testing and Ethical Hacking Linux Distribution",
                    "simple_name": "title",
                    "is_allowed": True
                },
                {
                    "name": "description",
                    "content": "Home of Kali Linux, an Advanced Penetration Testing Linux distribution used for Penetration Testing, Ethical Hacking and network security assessments.",
                    "simple_name": "description",
                    "is_allowed": True
                },
                {
                    "name": "description",
                    "content": "Home of Kali Linux, an Advanced Penetration Testing Linux distribution used for Penetration Testing, Ethical Hacking and network security assessments.",
                    "simple_name": "description",
                    "is_allowed": True
                },
                {
                    "name": "twitter:description",
                    "content": "Home of Kali Linux, an Advanced Penetration Testing Linux distribution used for Penetration Testing, Ethical Hacking and network security assessments.",
                    "simple_name": "description",
                    "is_allowed": True
                },
                {
                    "name": "og:description",
                    "content": "Home of Kali Linux, an Advanced Penetration Testing Linux distribution used for Penetration Testing, Ethical Hacking and network security assessments.",
                    "simple_name": "description",
                    "is_allowed": True
                },
                {
                    "name": "keywords",
                    "content": "kali,linux,kalilinux,Penetration,Testing,Penetration Testing,Distribution,Advanced",
                    "simple_name": "keywords",
                    "is_allowed": True
                },
                {
                    "name": "apple-mobile-web-app-status-bar-style",
                    "content": "black-translucent",
                    "simple_name": "apple-mobile-web-app-status-bar-style",
                    "is_allowed": False
                },
                {
                    "name": "msapplication-navbutton-color",
                    "content": "#367BF0",
                    "simple_name": "msapplication-navbutton-color",
                    "is_allowed": False
                },
                {
                    "name": "theme-color",
                    "content": "#367BF0",
                    "simple_name": "theme-color",
                    "is_allowed": False
                },
                {
                    "name": "language",
                    "content": "English",
                    "simple_name": "language",
                    "is_allowed": True
                },
                {
                    "name": "og:locale",
                    "content": "en_US",
                    "simple_name": "locale",
                    "is_allowed": True
                },
                {
                    "name": "image",
                    "content": "https://www.kali.org/images/kali-logo.svg",
                    "simple_name": "image",
                    "is_allowed": True
                },
                {
                    "name": "og:image",
                    "content": "https://www.kali.org/images/kali-logo.svg",
                    "simple_name": "image",
                    "is_allowed": True
                },
                {
                    "name": "twitter:image",
                    "content": "https://www.kali.org/images/kali-logo.svg",
                    "simple_name": "image",
                    "is_allowed": True
                },
                {
                    "name": "twitter:image:src",
                    "content": "https://www.kali.org/images/kali-logo.svg",
                    "simple_name": "image",
                    "is_allowed": True
                },
                {
                    "name": "og:updated_time",
                    "content": "2023-08-10T00:00:00Z",
                    "simple_name": "updated_time",
                    "is_allowed": True
                },
                {
                    "name": "twitter:site",
                    "content": "@kalilinux",
                    "simple_name": "site",
                    "is_allowed": True
                },
                {
                    "name": "twitter:creator",
                    "content": "@kalilinux",
                    "simple_name": "creator",
                    "is_allowed": True
                },
                {
                    "name": "twitter:url",
                    "content": "https://www.kali.org/",
                    "simple_name": "url",
                    "is_allowed": True
                },
                {
                    "name": "url",
                    "content": "https://www.kali.org/",
                    "simple_name": "url",
                    "is_allowed": True
                },
                {
                    "name": "og:url",
                    "content": "https://www.kali.org/",
                    "simple_name": "url",
                    "is_allowed": True
                }
            ],
        },
    )
    print(
        BookmarkWeightsSheet(bookmark, webpage).generate()
    )
