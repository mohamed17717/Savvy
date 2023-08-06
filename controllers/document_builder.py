from common.utils.dto import Bookmark, BookmarkWebpage


class BookmarkDocumentBuilder:
    def __init__(self, bookmark: Bookmark, webpage: BookmarkWebpage) -> None:
        self.bookmark = bookmark
        self.webpage = webpage

    def build(self):
        template = (
            f"[GET {self.webpage.url}]\n"
            f"\ntitle: {self.webpage.title}"
            f"\nsecondary_title: {self.bookmark.title}"
            f"\n\n{self.webpage.meta_data}"
            f"\ndomain: {self.bookmark.domain}"
        )
        return template
