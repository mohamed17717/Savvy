import os
from datetime import date

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


def validate_file_extension(*allowed_extensions: list[str]):
    def func(value):
        # allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif']
        extension = os.path.splitext(value.name)[1].lower()
        if extension not in allowed_extensions:
            raise ValidationError(
                _(f'Only {",".join(allowed_extensions)} files are allowed.'))
    return func


def validate_file_size(size_MB: int):
    def func(value):
        max_size = size_MB * 1024 * 1024  # 5MB
        if value.size > max_size:
            raise ValidationError(
                _(f'File size should not exceed {size_MB}MB.'))
    return func


def is_future_date_validator(value: date):
    today = date.today()
    if value < today:
        raise ValidationError('date must be in the future.')
