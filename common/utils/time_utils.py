from datetime import datetime

from django.utils.timezone import make_aware


def fromtimestamp(time):
    if not isinstance(time, int):
        time = int(time)
    return make_aware(datetime.fromtimestamp(time))
