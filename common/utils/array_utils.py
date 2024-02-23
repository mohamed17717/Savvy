from typing import Generator


def window_list(data: list, size: int, step: int = 1) -> Generator[list, None, None]:
    length = len(data)
    if length < size:
        size = length
    for i in range(0, length-size+1, step):
        yield data[i: i + size]


def unique_dicts_in_list(data: list[dict], key) -> list[dict]:
    return list({d[key]: d for d in data}.values())
