from typing import Generator


def window_list(data: list, size: int) -> Generator[list, None, None]:
    if size == 0:
        raise ZeroDivisionError

    length = len(data)
    if length < size:
        size = length
    for i in range(0, length, size):
        yield data[i : i + size]


def unique_dicts_in_list(data: list[dict], key) -> list[dict]:
    return list({d[key]: d for d in data}.values())
