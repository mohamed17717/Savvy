from functools import partial

from django.db import models
from django.db.models.signals import post_save, pre_save


class SignalsCustomManager(models.Manager):
    '''
    Custom manager to fire signals on create and bulk create
    '''

    def _trigger(self, objs):
        if not objs: return

        if not isinstance(objs, list):
            objs = [objs]

        signals = {
            'post_save': partial(post_save.send, sender=self.model, created=True),
            'pre_save': partial(pre_save.send, sender=self.model),
        }

        for signal in signals.values():
            for i in objs:
                signal(instance=i)

    def bulk_create(self, objs, **kwargs):
        result = super().bulk_create(objs, **kwargs)
        self._trigger(objs)
        return result
