import re
import string
import random


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

def adv_clean_string(string: str):
    ...
