from asgiref.sync import sync_to_async


@sync_to_async
def django_wrapper(func, *args, **kwargs):
    return func(*args, **kwargs)
