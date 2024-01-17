import hashlib
from django.db import models


def hash_file(file_field: models.FileField) -> str:
    hasher = hashlib.sha256()
    for chunk in iter(lambda: file_field.read(4096), b''):
        hasher.update(chunk)
    return hasher.hexdigest()
