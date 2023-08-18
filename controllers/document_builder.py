import re
from typing import Dict
from common.utils.dto import Bookmark, BookmarkWebpage


# Create WeightedDocumentBuilder
class BookmarkWeightedDocumentBuilder:
    def __init__(self, bookmark: Bookmark, webpage: BookmarkWebpage) -> None:
        self.bookmark = bookmark
        self.webpage = webpage

    def build(self) -> Dict[str, int]:
        # output is { word: weight }
        weight_sheet = (
            (self.webpage.url, 2),
            (self.webpage.title, 8),
            (self.bookmark.title, 5),
            (self.webpage.meta_data, 3),
            (self.bookmark.domain, 4),
        )

        weighted_words = {}
        for phrase, weight in weight_sheet:
            # remove punctuation
            phrase = re.sub(r'[^\w ]', ' ', phrase)
            # remove double spaces
            phrase = re.sub(r' {2,}', '', phrase)

            words = phrase.split(' ')
            for word in words:
                if weighted_words.get(word) is not None:
                    weighted_words[word] += weight
                else:
                    weighted_words[word] = weight

        return weighted_words


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
