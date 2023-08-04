from pprint import pprint
from controllers.link_collector import BrowserBookmark

from common.utils.files import dump_to_file



def main():
    bookmarks = BrowserBookmark('src/resources/bookmarks/firefox_bookmarks.html')
    # pprint(bookmarks.parse())
    json_bookmarks = bookmarks.to_json()
    dump_to_file('./bookmarks.json', json_bookmarks)


if __name__ == '__main__':
    main()