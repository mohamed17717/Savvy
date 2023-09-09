import re
import spacy
import nltk

from nltk.stem import PorterStemmer, SnowballStemmer
from nltk.stem.wordnet import WordNetLemmatizer

import arabicstopwords.arabicstopwords as ar_stops

from langdetect import detect
from iso639 import Lang

from common.utils.dto import Bookmark, BookmarkWebpage

class TextCleaner:
    # All methods should return self
    # it make a chain clean
    SPACY_NLP = spacy.load('en_core_web_sm')

    def __init__(self, text: str) -> None:
        self.text = text

    def html_entities(self) -> 'TextCleaner':
        self.text = re.sub(r'\&\w*;', '', self.text)
        return self

    def html_tags(self) -> 'TextCleaner':
        self.text = re.sub(r'<.*?>', '', self.text)
        return self

    def emails(self) -> 'TextCleaner':
        self.text = re.sub(r'[\w.+-]+@[\w-]+\.[\w.-]+', '', self.text)
        return self

    def usernames(self) -> 'TextCleaner':
        self.text = re.sub(r'@(\w+)', '', self.text)
        return self

    def links(self) -> 'TextCleaner':
        self.text = re.sub(r'(http|https|ftp)?:?\/\/\S*', '', self.text)
        return self

    def lowercase(self) -> 'TextCleaner':
        self.text = self.text.lower()
        return self

    def hashtags(self) -> 'TextCleaner':
        self.text = re.sub(r'#(\w+)', '', self.text)
        return self

    def repeating_chars(self) -> 'TextCleaner':
        # Remove repeating chars if it a word
        self.text = re.sub(r'\b(.)\1{2,}\b', r'', self.text)
        return self

    def not_letters(self) -> 'TextCleaner':
        # Remove anything that is not letters
        self.text = re.sub(r'[^\w\s]', ' ', self.text)
        return self

    def underscore(self) -> 'TextCleaner':
        self.text = re.sub(r'_', ' ', self.text)
        return self

    def numbers(self) -> 'TextCleaner':
        self.text = re.sub(r'\d', ' ', self.text)
        return self

    def lines(self) -> 'TextCleaner':
        self.text = re.sub(r'\n', ' ', self.text)
        return self

    def shorter_than(self, length=2) -> 'TextCleaner':
        # Remove anything that is less than two characters
        # r'\b\w{1}\b'
        pattern = r'\b\w{,%d}\b' % (length-1)
        self.text = re.sub(pattern, '', self.text)
        return self

    def stop_words(self, words=[], lang='english') -> 'TextCleaner':
        # remove this words
        words += {
            'english': lambda: (
                nltk.corpus.stopwords.words('english')
                + 'and,of,en,us,org,com,an,english,for,our'.split(',')
            ),
            'arabic': lambda: (
                nltk.corpus.stopwords.words("arabic")
                + ar_stops.stopwords_list()
            )
        }.get(lang, lambda: [])()

        words = set(words)
        words = '|'.join(words)

        # r'\b(and|of|en|us)\b'
        pattern = r'\b(%s)\b' % words
        self.text = re.sub(pattern, '', self.text)
        return self

    def double_spaces(self) -> 'TextCleaner':
        self.text = re.sub(r' {2,}', ' ', self.text)
        return self

    def stemming(self, lang='english', method='stem') -> 'TextCleaner':
        words = self.text.split(' ')

        if method == 'stem':
            # stemmer = PorterStemmer()
            stemmer = SnowballStemmer(lang)
            words = [stemmer.stem(word) for word in words]
        elif method == 'lem':
            lem = WordNetLemmatizer()
            words = [lem.lemmatize(y) for y in words]
        elif method == 'spacy':
            words = [word.lemma_ for word in self.SPACY_NLP(' '.join(words))]

        self.text = ' '.join(words)
        return self

    def translation(self) -> 'TextCleaner':
        # determine if its contain many langs
        # if yes determine which lang exists most
        # then translate others to this lang
        return self

    def spelling_correction(self) -> 'TextCleaner':
        return self

    def uncamelcase(self) -> 'TextCleaner':
        # add space before every uppercase
        self.text = re.sub(r'([A-Z])', r' \1', self.text)
        return self

    def _get_language(self):
        lang = detect(self.text)  # ai detect lang symbol
        lang = Lang(lang)  # symbol to name
        return lang.name.lower()

    def full_clean(self) -> 'TextCleaner':
        return (
            self.html_entities()
                .html_tags()
                .emails()
                .usernames()
                .links()
                .uncamelcase()
                .lowercase()
                .hashtags()
                .repeating_chars()
                .not_letters()
                .underscore()
                .numbers()
                .lines()
                .shorter_than()
                .stop_words()
                .double_spaces()
                .stemming(method='spacy')
        )


print(
    TextCleaner(
        '<span href="https://google.com">Mo Salah is a famous egyptian, &copy; who playing football'
        ' in liverpool with_number 11 and he l//**-oves @shakira website is a  a www.xnxxx.com</span>'
        '\n\n\n\n#never_walk_alone salah@yahoo.com\n\n\n\n'
    ).full_clean().text
)

class BookmarkWeightsSheet:
    SUFFIX = '_weight'
    PREFIX = '_'

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

    def filter_class_methods(self, prefix:str=None, suffix:str=None):
        methods = dir(self)

        if prefix:
            methods = filter(lambda i: i.startswith(prefix), methods)
        if suffix:
            methods = filter(lambda i: i.endswith(suffix), methods)

        methods = map(lambda i: getattr(self, i), methods)
        methods = filter(lambda i: type(i) == type(self.filter_class_methods), methods)
        methods = list(methods)

        return methods

    def generate(self):
        methods = self.filter_class_methods(self.PREFIX, self.SUFFIX)
        
        return [method() for method in methods]



class PhraseWordsWeight:
    # WEIGHTS_SHEET = {
    #     'url': (lambda bookmark: bookmark.url, weight:=8),
    #     'title': 8
    # }
    def __init__(self, weights_sheet: tuple[tuple]) -> None:
        self.weights_sheet = weights_sheet

    def weight(self):
        weights = []
        for phrase, weight in self.weights_sheet:
            weight = self.phrase_weight(phrase.split(' '), weight)
            weights.append(weight)
        return self.merge_dicts(*weights)

    @staticmethod
    def phrase_weight(phrase: list[str], weight: int):
        weighted_words = {}
        for word in phrase:
            if weighted_words.get(word) is None:
                weighted_words[word] = weight
            else:
                weighted_words[word] += weight
        return

    @staticmethod
    def merge_dicts(d1: dict, *args: dict, method=lambda a,b: a+b):
        result = d1.copy()
        for d2 in args:
            for key, value in d2.items():
                stored_value = result.get(key) 
                if stored_value is None:
                    result[key] = value
                else:
                    result[key] = method(stored_value, value)
        return result           

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
