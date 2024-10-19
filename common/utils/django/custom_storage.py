import os

from django.conf import settings
from django.contrib.staticfiles.storage import StaticFilesStorage


class CustomStaticFilesStorage(StaticFilesStorage):
    def path(self, name):
        abs_path = os.path.abspath(name)
        abs_static_dirs = map(os.path.abspath, settings.STATICFILES_DIRS)
        checks = map(abs_path.startswith, abs_static_dirs)

        return None if any(checks) and name.endswith(".html") else super().path(name)

    def exists(self, name):
        return False if self.path(name) is None else super().exists(name)
