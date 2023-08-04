from pprint import pprint
from controllers.link_collector import BrowserBookmark

from common.utils.files import dump_to_file



def main():
    controller = BrowserBookmark('resources/bookmarks/firefox_bookmarks.html')
    bookmarks = controller.from_html()
    json_bookmarks = controller.to_json(bookmarks)
    dump_to_file('./bookmarks.json', json_bookmarks)


if __name__ == '__main__':
    main()