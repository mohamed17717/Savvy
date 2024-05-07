import numpy as np


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


def extend_matrix(mx1, mx2, intersected_mx):
    """used to combine 2 matrices with intersection between them"""
    mx1 = np.vstack((mx1, intersected_mx))
    intersected_mx = np.rot90(intersected_mx, k=1)[::-1]
    intersected_mx = np.vstack((intersected_mx, mx2))
    mx1 = np.hstack((mx1, intersected_mx))
    return mx1
