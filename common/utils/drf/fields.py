from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework import serializers


class CustomFileField(serializers.Field):
    """To handle the flow of uploading file first
    then send its url inside the json payload later"""

    def to_internal_value(self, data):
        upload_to = getattr(self.parent.Meta.model, self.source).field.upload_to

        image = default_storage.open(data)
        content = image.read()
        image_name = image.name.split("/")[-1]

        path = default_storage.save(upload_to + image_name, ContentFile(content))
        return path

    def to_representation(self, value):
        # Return the path to the image as the representation
        return value.name
