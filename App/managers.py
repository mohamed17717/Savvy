from django.db import models
from django.db.models.signals import post_save, pre_save

from App import controllers


class BulkSignalsQuerySet(models.QuerySet):
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

    def bulk_update(self, objs, fields, **kwargs) -> int:
        raise NotImplementedError(
            'This manage not support using `.bulk_update()` instead use `.update()`')

    def update(self, **kwargs) -> int:
        objs = list(self)
        for obj in objs:
            for k, v in kwargs.items():
                setattr(obj, k, v)

        self._trigger_pre_save(objs)
        result = super().update(**kwargs)
        self._trigger_post_save(objs)

        return result


class BookmarkQuerySet(models.QuerySet):
    def bulk_create(self, objs, **kwargs):
        result = super().bulk_create(objs, **kwargs)

        if result:
            user = result[0].user
            publisher = controllers.BookmarkRedisPublisher(user)
            for obj in result:
                publisher.publish(
                    {'bookmark_id': obj.id, 'status': obj.process_status}
                )

        return result

    def update_process_status(self, new_status) -> int:
        objs = list(self)
        if not objs:
            return 0

        publisher = controllers.BookmarkRedisPublisher(objs[0].user)
        for obj in objs:
            if obj.process_status >= new_status:
                continue
            obj.process_status = new_status
            publisher.publish(
                {'bookmark_id': obj.id, 'status': new_status}
            )

        return self.bulk_update(objs, ['process_status'])
