from datetime import date

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils.deconstruct import deconstructible

User = get_user_model()


@deconstructible
class FileSizeValidator:
    def __init__(self, size_MB: int):
        self.size_MB = size_MB

    def __call__(self, value):
        max_size = self.size_MB * 1024 * 1024  # 5MB
        if value.size > max_size:
            raise ValidationError(
                _(f'File size should not exceed {self.size_MB}MB.'))


def is_future_date_validator(value: date):
    today = date.today()
    if value < today:
        raise ValidationError('date must be in the future.')
