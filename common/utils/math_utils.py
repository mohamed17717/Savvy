def balanced_avg(length1, avg1, length2, avg2):
    avg = (avg1 * length1 + avg2 * length2) / (length1 + length2)
    return round(avg, 3)


def minmax(num, bottom, top):
    num = min(num, top)
    num = max(num, bottom)
    return num
