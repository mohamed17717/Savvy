from typing import Any
from django.db import models
from django.db.models.signals import post_save, pre_save


class SignalsCustomManager(models.Manager):
    '''Custom manager to fire signals on bulk create and update'''

    def _trigger_pre_save(self, objs):
        for obj in objs:
            pre_save.send(sender=self.model, instance=obj)

    def _trigger_post_save(self, objs, created=False):
        for obj in objs:
            post_save.send(sender=self.model, instance=obj, created=created)

    def bulk_create(self, objs, **kwargs):
        self._trigger_pre_save(objs)
        result = super().bulk_create(objs, **kwargs)
        self._trigger_post_save(objs, created=True)
        return result

    def bulk_update(self, objs, fields, **kwargs):
        self._trigger_pre_save(objs)
        result = super().bulk_update(objs, fields, **kwargs)
        self._trigger_post_save(objs)
        return result

    def update(self, **kwargs: Any) -> int:
        queryset = self.get_queryset()
        objs = list(queryset)
        self._trigger_pre_save(objs)
        result = super().update(**kwargs)
        self._trigger_post_save(objs)
        
        return result
