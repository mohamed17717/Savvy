import re
import spacy
import nltk

from nltk.stem import PorterStemmer, SnowballStemmer
from nltk.stem.wordnet import WordNetLemmatizer

import arabicstopwords.arabicstopwords as ar_stops

from langdetect import detect
from iso639 import Lang


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
        self.text = re.sub(r'([A-Z])', r' \1',self.text)
        return self

    def _get_language(self):
        lang = detect(self.text) # ai detect lang symbol
        lang = Lang(lang) # symbol to name
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

class TextWeight:
    # Should be constant in settings contain all this shit
    ...

