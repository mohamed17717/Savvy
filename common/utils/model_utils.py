from datetime import date

from django.db import transaction
from django.db.utils import IntegrityError
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


def concurrent_get_or_create(model, **kwargs):
    with transaction.atomic():
        try:
            obj, created = model.objects.get_or_create(**kwargs)
            return obj, created
        except IntegrityError:
            # Handle the exception if a duplicate is trying to be created
            kwargs.pop('defaults', None)
            obj = model.objects.select_for_update().get(**kwargs)
            return obj, False


def clone(instance):
    instance.pk = None
    instance.save()

    return instance


def bulk_clone(qs, changes: dict):
    model = qs.model
    instances = []
    for instance in qs:
        instance.pk = None
        for field, value in changes.items():
            setattr(instance, field, value)
        instances.append(instance)

    return model.objects.bulk_create(instances)
