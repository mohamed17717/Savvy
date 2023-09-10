
def get_by_alias(_dict: dict, alias_keys: list[str], default=None):
    for key in alias_keys:
        if _dict.get(key) is not None:
            return _dict[key]
    return default


def stringify_dict(_dict: dict) -> str:
    data = ''
    for key, value in _dict.items():
        data += f'{key}: {value}\n'
    return data


def merge_dicts(d1: dict, *args: dict, method=lambda a, b: a+b):
    result = d1.copy()
    for d2 in args:
        for key, value in d2.items():
            stored_value = result.get(key)
            if stored_value is None:
                result[key] = value
            else:
                result[key] = method(stored_value, value)
    return result
