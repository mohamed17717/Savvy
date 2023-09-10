import types


def filter_class_methods(obj, prefix: str = None, suffix: str = None):
    methods = dir(obj)

    if prefix:
        methods = filter(lambda i: i.startswith(prefix), methods)
    if suffix:
        methods = filter(lambda i: i.endswith(suffix), methods)

    methods = map(lambda i: getattr(obj, i), methods)
    methods = filter(lambda i: type(i) == types.MethodType, methods)
    methods = list(methods)

    return methods
