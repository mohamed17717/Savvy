import json
import asyncio
from datetime import datetime

from .redis_utils import RedisPubSub


class UserProgressSingleton:
    _instances = {}  # {user_id : instance}
    _lock = asyncio.Lock()

    def __init__(self, user_id):
        if self._instances.get(user_id) is not None:
            raise Exception('UserProgressSingleton instance already exists')

        self.user_id = user_id

        self.created = datetime.now()
        self.total = None
        self.individual_progress = {}
        self.individual_limit = 80
        self.message = ''

    @property
    def progress(self):
        if self.total in [None, 0]:
            raise Exception('Total is not set')

        total_progress = sum(
            self.individual_progress.values()) / self.individual_limit
        return total_progress / self.total * 100

    def set_total(self, total):
        if self.total is None:
            self.total = 0
        self.total += total

    def change(self, data):
        if data['type'] == RedisPubSub.MessageTypes.FILE_UPLOAD:
            total = data['total_bookmarks']
            self.set_total(total)
            self.message = f'new uploaded bookmarks: {total}'
        elif data['type'] == RedisPubSub.MessageTypes.BOOKMARK_CHANGE:
            bookmark_id = data['bookmark_id']
            status = data['status']
            self.individual_progress[bookmark_id] = status
            self.message = f'bookmark {bookmark_id} status: {status/80*100}%'
        # elif data['type'] == 3:
            # TODO django should send this type

    def __str__(self):
        data = {
            'total': self.total,
            'progress': self.progress,
            'message': self.message,
        }
        return json.dumps(data)

    @classmethod
    async def get_instance(cls, user_id) -> 'UserProgressSingleton':
        async with cls._lock:
            _instance = cls._instances.get(user_id)
            if _instance is None:
                _instance = cls(user_id)
                cls._instances[user_id] = _instance
            return _instance
