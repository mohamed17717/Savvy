import json
import asyncio
import uuid

from datetime import datetime, timedelta

from fastapi import Request
from sse_starlette.sse import EventSourceResponse

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
        self.DONE = False

    @property
    def progress(self) -> float:
        if self.total in [None, 0]:
            raise ValueError('Total is not set')

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

        self.DONE = self.progress >= 100
        if self.DONE:
            self.message = 'All bookmarks are uploaded'

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
            return _instance

    @classmethod
    async def get_or_create_instance(cls, user_id) -> 'UserProgressSingleton':
        async with cls._lock:
            _instance = cls._instances.get(user_id)
            if _instance is None:
                _instance = cls(user_id)
                cls._instances[user_id] = _instance
            return _instance


class ProgressSSE:
    MESSAGE_STREAM_DELAY = 0.4  # second

    def __init__(self, user_progress: UserProgressSingleton):
        self.user_progress = user_progress
        self.progress = 0

    def wrap_message(self, data):
        return json.dumps({
            "event": "progress",
            "id": uuid.uuid4().hex,
            "retry": self.MESSAGE_STREAM_RETRY_TIMEOUT,
            "data": data,
        })

    async def event_loop(self, request: Request):
        force_break_time = datetime.utcnow() + timedelta(hours=3)

        while datetime.utcnow() < force_break_time:
            if await request.is_disconnected():
                break

            progress = self.user_progress.progress
            # progress changed
            if self.progress != progress:
                self.progress = progress

                message = str(self.user_progress)
                yield f'data: {self.wrap_message(message)}\n\n'

                if self.user_progress.DONE:
                    break

            await asyncio.sleep(self.MESSAGE_STREAM_DELAY)

    async def stream(self, request: Request):
        return EventSourceResponse(self.event_loop(request))
