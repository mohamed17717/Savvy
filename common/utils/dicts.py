
def get_by_alias(_dict: dict, alias_keys: list[str], default=None):
    for key in alias_keys:
        if _dict.get(key) is not None:
            return _dict[key]
    return default
