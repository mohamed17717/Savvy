import threading
from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.utils import IntegrityError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

User = get_user_model()


@deconstructible
class FileSizeValidator:
    def __init__(self, size_MB: int):
        self.size_MB = size_MB

    def __call__(self, value):
        max_size = self.size_MB * 1024 * 1024  # 5MB
        if value.size > max_size:
            raise ValidationError(_(f"File size should not exceed {self.size_MB}MB."))


def is_future_date_validator(value: date):
    today = date.today()
    if value < today:
        raise ValidationError("date must be in the future.")


def concurrent_get_or_create(model, **kwargs):
    with transaction.atomic():
        try:
            obj, created = model.objects.get_or_create(**kwargs)
            return obj, created
        except IntegrityError:
            # Handle the exception if a duplicate is trying to be created
            kwargs.pop("defaults", None)
            obj = model.objects.select_for_update().get(**kwargs)
            return obj, False


def clone(instance, **kwargs):
    instance.pk = None
    for field, value in kwargs.items():
        setattr(instance, field, value)
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


class CentralizedBulkCreator:
    def __init__(self, model, m2m_fields: list[str]):
        self.model = model
        self.m2m_fields = m2m_fields
        self.m2m_models = {
            m2m_field: getattr(self.model, m2m_field).through
            for m2m_field in m2m_fields
        }
        self.data = {
            "objects": [],
            "m2m_objects": [],  # [{bookmarks: [], tags: []}, ...]
        }
        self.has_post_calculation = hasattr(model, "post_create")
        # max objects
        self.max_objects = 500

        # time handling
        self.max_time = 10
        self.lock = threading.Lock()
        self.timer = None

    def __del__(self):
        self.flush()

    def add(self, obj, m2m_objects: dict = {}):
        with self.lock:
            self.data["objects"].append(obj)
            self.data["m2m_objects"].append(m2m_objects)

        if len(self.data["objects"]) >= self.max_objects:
            self.flush()

        self.reset_timer()

    def cancel_timer(self):
        if self.timer:
            self.timer.cancel()
            self.timer = None

    def reset_timer(self):
        self.cancel_timer()

        self.timer = threading.Timer(self.max_time, self.flush)
        self.timer.start()

    def reset_data(self):
        self.data = {
            "objects": [],
            "m2m_objects": [],  # [{bookmarks: [], tags: []}, ...]
        }

    def bulk_create_m2m(self, objects):
        m2m_bulk_data = {m2m_field: [] for m2m_field in self.m2m_fields}

        for obj, m2m_objects in zip(objects, self.data["m2m_objects"]):
            for m2m_field, m2m_data_array in m2m_objects.items():
                m2m_model = self.m2m_models[m2m_field]
                m2m_model_fields = map(lambda i: i.name + "_id", m2m_model._meta.fields)
                _, instance_field_name, related_field_name = list(m2m_model_fields)

                for m2m_object in m2m_data_array:
                    m2m_object_kwargs = {
                        instance_field_name: obj.id,
                        related_field_name: m2m_object.id,
                    }
                    m2m_bulk_data[m2m_field].append(m2m_model(**m2m_object_kwargs))

        for field, data in m2m_bulk_data.items():
            self.m2m_models[field].objects.bulk_create(data, batch_size=500)

    def flush(self) -> None:
        with self.lock:
            objects = self.data["objects"]

            if not objects:
                return

            objects = self.model.objects.bulk_create(objects, batch_size=500)

            if self.has_post_calculation:
                updated_fields = set()
                for obj in objects:
                    updated_fields.add(*obj.post_create())
                self.model.objects.bulk_update(objects, updated_fields)

            self.bulk_create_m2m(objects)
            self.reset_data()
            self.cancel_timer()
