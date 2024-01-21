import string
import random


def random_string(length=6) -> str:
    space = string.ascii_lowercase + string.digits
    return ''.join(random.choices(space, k=length))
