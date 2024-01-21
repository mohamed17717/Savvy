def filter_row_length_in_matrix(mx, gt=None, lt=None, gte=None, lte=None, eq=None):
    conditions = (
        (gt, lambda row: len(row) > gt),
        (lt, lambda row: len(row) < lt),
        (gte, lambda row: len(row) >= gte),
        (lte, lambda row: len(row) <= lte),
        (eq, lambda row: len(row) == eq),
    )
    conditions = [func for k, func in conditions if k is not None]

    def check(row):
        return all(func(row) for func in conditions)

    return filter(check, mx)


def flat_matrix(mx):
    flat = []
    for row in mx:
        flat.extend(row)
    return flat
