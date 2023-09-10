def list_counter(ls, step=1) -> dict:
    counter = {}
    for i in ls:
        if counter.get(i) is None:
            counter[i] = step
        else:
            counter[i] += step
    return counter
