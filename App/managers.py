from django.db import models
from django.db.models.signals import post_save, pre_save

from realtime.common.redis_utils import RedisPubSub


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
    def by_user(self, user):
        return self.filter(user=user)

    def bulk_create(self, objs, **kwargs):
        result = super().bulk_create(objs, **kwargs)

        if result:
            user = result[0].user
            for obj in result:
                RedisPubSub.pub({
                    'type': RedisPubSub.MessageTypes.BOOKMARK_CHANGE,
                    'user_id': user.id,
                    'bookmark_id': obj.id,
                    'status': obj.process_status
                })

        return result

    def update_process_status(self, new_status) -> int:
        objs = list(self)
        if not objs:
            return 0

        user_id = objs[0].user.id
        for obj in objs:
            if obj.process_status >= new_status:
                continue
            obj.process_status = new_status
            RedisPubSub.pub({
                'type': RedisPubSub.MessageTypes.BOOKMARK_CHANGE,
                'user_id': user_id,
                'bookmark_id': obj.id,
                'status': new_status
            })

        return self.bulk_update(objs, ['process_status'])

    def start_cluster(self) -> int:
        from App.models import Bookmark
        return self.update_process_status(Bookmark.ProcessStatus.START_CLUSTER.value)

    def clustered(self) -> int:
        from App.models import Bookmark
        return self.update_process_status(Bookmark.ProcessStatus.CLUSTERED.value)

    def start_text_processing(self) -> int:
        from App.models import Bookmark
        return self.update_process_status(Bookmark.ProcessStatus.START_TEXT_PROCESSING.value)

    def text_processed(self) -> int:
        from App.models import Bookmark
        return self.update_process_status(Bookmark.ProcessStatus.TEXT_PROCESSED.value)

    def start_crawl(self) -> int:
        from App.models import Bookmark
        return self.update_process_status(Bookmark.ProcessStatus.START_CRAWL.value)

    def crawled(self) -> int:
        from App.models import Bookmark
        return self.update_process_status(Bookmark.ProcessStatus.CRAWLED.value)


class BookmarkManager(models.Manager):
    def get_queryset(self):
        return BookmarkQuerySet(self.model, using=self._db).filter(hidden=False)


class BookmarkHiddenManager(models.Manager):
    def get_queryset(self):
        return BookmarkQuerySet(self.model, using=self._db).filter(hidden=True)


class AllBookmarkManager(models.Manager):
    def get_queryset(self):
        return BookmarkQuerySet(self.model, using=self._db)
