def window_list(data: list, size: int, step: int = 1) -> list:
    length = len(data)
    if length < size:
        size = length
    for i in range(0, length-size+1, step):
        yield data[i: i + size]
