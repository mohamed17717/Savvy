import hashlib
import os
import secrets

from django.db import models


def hash_file(file_field: models.FileField) -> str:
    hasher = hashlib.sha256()
    for chunk in iter(lambda: file_field.read(4096), b""):
        hasher.update(chunk)
    return hasher.hexdigest()


def random_filename(path, ext="html"):
    def generate():
        new_name = f"{secrets.token_hex(12)}.{ext}"
        return os.path.join(path, new_name)

    file_path = generate()
    while os.path.exists(file_path):
        file_path = generate()

    return file_path
