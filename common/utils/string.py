import re
import string
import random

import nltk
from nltk.stem import PorterStemmer
from nltk.stem.wordnet import WordNetLemmatizer
import spacy
import arabicstopwords.arabicstopwords as stp


def random_string() -> str:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))


def clean_string(string: str) -> str:
    # TODO make it a class and chain the pipes on it
    # so you apply only pipes you need
    # also with ability to return the substituted text

    # Remove HTML entities
    tmp = re.sub(r'\&\w*;', '', string)
    # Remove html tags
    tmp = re.sub(r'<.*?>', '', tmp)
    # Remove email
    tmp = re.sub(r'[\w.+-]+@[\w-]+\.[\w.-]+', '', tmp)
    # Remove @user
    tmp = re.sub(r'@(\w+)', '', tmp)
    # Remove links
    tmp = re.sub(r'(http|https|ftp)?:?\/\/\S*', '', tmp)
    # Lowercase
    tmp = tmp.lower()
    # Remove Hashtags
    tmp = re.sub(r'#(\w+)', '', tmp)
    # Remove repeating chars
    tmp = re.sub(r'(.)\1{2,}', r'', tmp)
    # Remove anything that is not letters
    tmp = re.sub(r'[^\w\s]', ' ', tmp)
    # Remove Underscore
    tmp = re.sub(r'_', ' ', tmp)
    # Remove Numbers
    tmp = re.sub(r'\d', ' ', tmp)
    # Remove lines
    tmp = re.sub(r'\n', ' ', tmp)
    # Remove anything that is less than two characters
    tmp = re.sub(r'\b\w{1}\b', '', tmp)
    # Remove multiple spaces
    # tmp = re.sub(r'\s\s+', ' ', tmp)
    # remove this words
    tmp = re.sub(r'\b(and|of|en|us|org|com|an|english|for|our)\b', '', tmp)
    # remove double spaces
    tmp = re.sub(r' {2,}', ' ', tmp)

    return tmp.strip()


def adv_clean_string(string: str, stem: str = 'None'):
    # Remove stop words
    text = text.split()
    useless_words = nltk.corpus.stopwords.words("english")
    # arabic_words = nltk.corpus.stopwords.words("arabic")
    # arabic_words = stp.stopwords_list()
    useless_words = useless_words + ['hi', 'im']

    text_filtered = [word for word in text if not word in useless_words]

    # Stem or Lemmatize
    if stem == 'Stem':
        stemmer = PorterStemmer()
        text_stemmed = [stemmer.stem(y) for y in text_filtered]
    elif stem == 'Lem':
        lem = WordNetLemmatizer()
        text_stemmed = [lem.lemmatize(y) for y in text_filtered]
    elif stem == 'Spacy':
        # This line should loaded outside
        nlp = spacy.load('en_core_web_sm')

        text_filtered = nlp(' '.join(text_filtered))
        text_stemmed = [y.lemma_ for y in text_filtered]
    else:
        text_stemmed = text_filtered

    final_string = ' '.join(text_stemmed)

    # for more steps check this
    # https://monkeylearn.com/blog/text-cleaning/
    return final_string
