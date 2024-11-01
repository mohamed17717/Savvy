import contextlib
import glob
import os
import shutil

from django.db import models as dj_models

from App import models


def delete_everything():
    for model_name in dir(models):
        model = getattr(models, model_name)
        with contextlib.suppress(Exception):
            if issubclass(model, dj_models.Model) and "App" in model.__module__:
                print("Start deleting", model)
                model.objects.all().delete()


def system_zero():
    for f in glob.glob("./logs/*.log"):
        print("[remove] ", f)
        os.remove(f)
    for d in glob.glob("./media/*"):
        print("[remove] ", d)
        shutil.rmtree(d)
    print("delete database")
    delete_everything()


# def export_services_logs():
# not work from shell
# services = [
#     "django",
#     "celery_orm_worker",
#     "celery_scrapy_worker",
#     "celery_download_images_worker",
# ]
# for s in services:
# os.system(f"docker-compose logs {s} > {s}.log")
