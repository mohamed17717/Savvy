def balanced_avg(length1, avg1, length2, avg2):
    return (avg1 * length1 + avg2 * length2) / (length1 + length2)


def dynamic_number_boundaries(num, bottom, top):
    if num > top:
        num = top
    if num < bottom:
        num = bottom
    return num
