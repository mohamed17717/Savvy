import string
import random


def random_string(length=6) -> str:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
