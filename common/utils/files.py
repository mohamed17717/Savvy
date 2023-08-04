def load_file(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        data = f.read()
    return data

def dump_to_file(path: str, data: str) -> str:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(data)

