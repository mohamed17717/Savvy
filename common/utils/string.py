import string
import random


def random_string() -> str:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
