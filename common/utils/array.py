def window_list(data: list, size: int, step: int = 1) -> list:
    for i in range(0, len(data)-size+1, step):
        yield data[i: i + size]
