import contextlib

from django.db import models as dj_models

from App import models

# delete all data
for model in dir(models):
    model = getattr(models, model)
    with contextlib.suppress(Exception):
        if issubclass(model, dj_models.Model) and "App" in model.__module__:
            print("Start deleting", model)
            model.objects.all().delete()
