import re
import spacy
import nltk

from nltk.stem import PorterStemmer, SnowballStemmer
from nltk.stem.wordnet import WordNetLemmatizer

import arabicstopwords.arabicstopwords as ar_stops

from langdetect import detect
from iso639 import Lang


class TextCleaner:
    # TODO make 2 classes one cleaning and one extracting
    # All methods should return self
    # it make a chain clean
    SPACY_NLP = spacy.load('en_core_web_sm')

    def __init__(self, text: str) -> None:
        self.text = text.strip()

    def html_entities(self) -> 'TextCleaner':
        self.text = re.sub(r'\&\w*;', '', self.text).strip()
        return self

    def html_tags(self) -> 'TextCleaner':
        self.text = re.sub(r'<.*?>', '', self.text).strip()
        return self

    def emails(self) -> 'TextCleaner':
        self.text = re.sub(r'[\w.+-]+@[\w-]+\.[\w.-]+', '', self.text).strip()
        return self

    def usernames(self) -> 'TextCleaner':
        self.text = re.sub(r'@([\.\w]+)', '', self.text).strip()
        return self

    def links(self) -> 'TextCleaner':
        self.text = re.sub(r'(http|https|ftp)?:?\/\/\S*',
                           '', self.text).strip()
        return self

    def lowercase(self) -> 'TextCleaner':
        self.text = self.text.lower().strip()
        return self

    def hashtags(self) -> 'TextCleaner':
        self.text = re.sub(r'#(\w+)', r'\1', self.text).strip()
        return self

    def repeating_chars(self) -> 'TextCleaner':
        # Remove repeating chars if it a word
        self.text = re.sub(r'\b(.)\1{2,}\b', r'', self.text).strip()
        return self

    def not_letters(self) -> 'TextCleaner':
        # Remove anything that is not letters
        self.text = re.sub(r'[^\w\s]', ' ', self.text).strip()
        return self

    def underscore(self) -> 'TextCleaner':
        self.text = re.sub(r'_', ' ', self.text).strip()
        return self

    def numbers(self) -> 'TextCleaner':
        self.text = re.sub(r'\d', ' ', self.text).strip()
        return self

    def lines(self) -> 'TextCleaner':
        self.text = re.sub(r'\n', ' ', self.text).strip()
        return self

    def shorter_than(self, length=2) -> 'TextCleaner':
        # Remove anything that is less than two characters
        # r'\b\w{1}\b'
        pattern = r'\b\w{,%d}\b' % (length-1)
        self.text = re.sub(pattern, '', self.text).strip()
        return self

    def longer_than(self, length=20) -> 'TextCleaner':
        # Remove anything that is less than two characters
        # r'\b\w{1}\b'
        pattern = r'\b\w{%d,}\b' % (length)
        self.text = re.sub(pattern, '', self.text).strip()
        return self

    def stop_words(self, words=[], lang='english') -> 'TextCleaner':
        # remove this words
        words += {
            'english': lambda: (
                nltk.corpus.stopwords.words('english')
                + 'and,of,en,us,org,com,an,english,for,our'.split(',')
                + ['use', 'home', 'being', 'repo', 'php', 'let',
                   'day', 'month', 'week', 'year', 'second', 'minute',
                   'non', 'please', 'id', 'key', 'click', 'data', 'create',
                   'co', 'find', 'full', 'oct', 'unsupported', 'browser', 'width',
                   'sign', 'login', 'without'
                   ]
            ),
            'arabic': lambda: (
                nltk.corpus.stopwords.words("arabic")
                + ar_stops.stopwords_list()
            )
        }.get(lang, lambda: [])()

        words = set(words)
        self.text = ' '.join(set(self.text.split(' ')).difference(words))
        return self

    def double_spaces(self) -> 'TextCleaner':
        self.text = re.sub(r' {2,}', ' ', self.text).strip()
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

        self.text = ' '.join(words).strip()
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
        self.text = re.sub(r'([a-z])([A-Z])', r'\1 \2', self.text).strip()
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
