from common.utils.dto import Bookmark, BookmarkWebpage
from common.utils.dicts import merge_dicts
from common.utils.list_utils import list_counter
from common.utils.class_utils import filter_class_methods


class BookmarkWeightsSheet:
    PREFIX = '_'
    SUFFIX = '_weight'

    def __init__(self, bookmark: Bookmark, webpage: BookmarkWebpage) -> None:
        self.bookmark = bookmark
        self.webpage = webpage

    def _url_weight(self):
        return self.webpage.url, 2

    def _title_weight(self):
        return self.webpage.title, 8

    def _second_title_weight(self):
        return self.bookmark.title, 5

    def _webpage_meta_data_weight(self):
        return self.bookmark.domain, 3

    def _domain_weight(self):
        return self.bookmark.domain, 4

    def generate(self):
        methods = filter_class_methods(self, self.PREFIX, self.SUFFIX)
        return [method() for method in methods]


class PhraseWordsWeight:
    def __init__(self, weights_sheet: tuple[tuple]) -> None:
        self.weights_sheet = weights_sheet

    def weight(self):
        weights = []
        for phrase, weight in self.weights_sheet:
            weight = list_counter(phrase.split(' '), weight)
            weights.append(weight)
        return merge_dicts(*weights)
