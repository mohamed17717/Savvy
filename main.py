import os

from pprint import pprint
from controllers.link_collector import BrowserBookmark

from common.utils.files import dump_to_file



def main():
    # make sure that iam in base dir `src`
    if os.getcwd().endswith('src') is False:
        os.chdir('./src')

    controller = BrowserBookmark('resources/bookmarks/firefox_bookmarks.html')
    bookmarks = controller.from_html()
    json_bookmarks = controller.to_json(bookmarks)
    dump_to_file('../bookmarks.json', json_bookmarks)


if __name__ == '__main__':
    main()