
def mx_minimum_length(mx, length, eq=False):
    def condition(row): return len(row) > length
    if eq:
        def condition(row): return len(row) >= length

    return (row for row in mx if condition(row))


def mx_maximum_length(mx, length, eq=False):
    def condition(row): return len(row) < length
    if eq:
        def condition(row): return len(row) <= length

    return (row for row in mx if condition(row))


def mx_length_between(mx, top, bottom):
    return (row for row in mx if top > len(row) > bottom)


def mx_flat(mx):
    flat = []
    for row in mx:
        flat.extend(row)
    return flat
