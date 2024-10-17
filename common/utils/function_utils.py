def single_to_plural(func):
    """Higher order function to convert normal function
    to plural one that executed on the lists and accept
    list of arg
    """
    return lambda arr: list(map(func, arr))
