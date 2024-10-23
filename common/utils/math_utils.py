def minmax(num, bottom, top):
    if bottom > top:
        raise ValueError

    num = min(num, top)
    num = max(num, bottom)
    return num
