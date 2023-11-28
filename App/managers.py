from django.db import models
from django.db.models.signals import post_save


class SignalsCustomManager(models.Manager):
    '''
    Custom manager to fire signals on create and bulk create
    '''
    def bulk_create(self, objs, **kwargs):
        results = super().bulk_create(objs, **kwargs)

        # to make sure signals are saved
        for i in objs:
            post_save.send(i.__class__, instance=i, created=True)

        return results
