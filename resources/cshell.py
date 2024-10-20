import contextlib
import glob
import os
import shutil

from django.db import models as dj_models
from django.db.models import Count

from App import models


def one_bookmark_cluster():
    return models.Cluster.objects.filter(bookmarks_count=1)


def cluster_related_to_tag(tag_name):
    return models.Cluster.objects.filter(bookmarks__tags__name=tag_name).distinct()


def cluster_by_name(name):
    return models.Cluster.objects.get(name=name)


def how_it_look(cluster_name, index):
    cluster = cluster_by_name(cluster_name)
    bookmark = cluster.bookmarks.all()[index]
    html_file = bookmark.scrapes.last().html_file
    return f"http://localhost{html_file.url}", bookmark


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


# cluster_duplicates_bookmarks().count() # 168
# one_bookmark_cluster().count() # 234

# c_name = 'cluster power 0.567 contain 9 items'
# pprint(words_vectors_for_cluster(c_name))
# how_it_look(c_name, 1)
