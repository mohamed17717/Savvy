
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
