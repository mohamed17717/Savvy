import os
import redis
import json
from redis import asyncio as aioredis

from pydantic import BaseModel, Field


class RedisPubSub:
    CHANNEL_NAME = os.getenv('PUB_SUB_CHANNEL_NAME')
    HOST = os.getenv('REDIS_HOST')
    PORT = os.getenv('REDIS_PORT')

    clients = {
        'sync': redis.Redis(host=HOST, port=PORT, db=0),
        'async': aioredis.from_url(f'redis://{HOST}:{PORT}', encoding="utf-8", decode_responses=True)
    }

    class MessageTypes:
        INIT_UPLOAD = 0
        FILE_UPLOAD = 1
        BOOKMARK_CHANGE = 2
        FINISH = 3

    class InitUploadData(BaseModel, extra='allow'):
        user_id: int
        type: int = Field(
            default_factory=lambda: RedisPubSub.MessageTypes.INIT_UPLOAD)

    class FileUploadData(BaseModel, extra='allow'):
        user_id: int
        total_bookmarks: int
        type: int = Field(
            default_factory=lambda: RedisPubSub.MessageTypes.FILE_UPLOAD)

    class BookmarkChangeData(BaseModel, extra='allow'):
        user_id: int
        bookmark_id: int
        status: int
        type: int = Field(
            default_factory=lambda: RedisPubSub.MessageTypes.BOOKMARK_CHANGE)

    class FinishData(BaseModel, extra='allow'):
        user_id: int
        type: int = Field(
            default_factory=lambda: RedisPubSub.MessageTypes.FINISH)

    @classmethod
    def __validate_data(cls, data: dict) -> dict:
        _type = data.get('type')
        if _type is None:
            raise ValueError('type is required')
        elif _type == cls.MessageTypes.INIT_UPLOAD:
            data = cls.InitUploadData(**data)
        elif _type == cls.MessageTypes.FILE_UPLOAD:
            data = cls.FileUploadData(**data)
        elif _type == cls.MessageTypes.BOOKMARK_CHANGE:
            data = cls.BookmarkChangeData(**data)
        elif _type == cls.MessageTypes.FINISH:
            data = cls.FinishData(**data)
        else:
            raise ValueError('invalid type')

        return data.dict()

    @classmethod
    def pub(cls, data: dict) -> None:
        data = cls.__validate_data(data)
        client = cls.clients['sync']
        client.publish(cls.CHANNEL_NAME, json.dumps(data))

    @classmethod
    async def sub(cls, callback):
        client = cls.clients['async']
        pubsub = client.pubsub()
        await pubsub.subscribe(cls.CHANNEL_NAME)
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message['type'] == 'message':
                await callback(json.loads(message['data']))


class Publish:
    """Work as shortcut for publish messages"""

    @staticmethod
    def init_upload(user_id: int):
        RedisPubSub.pub({
            'type': RedisPubSub.MessageTypes.INIT_UPLOAD,
            'user_id': user_id,
        })

    @staticmethod
    def start_file(user_id, total_bookmarks):
        RedisPubSub.pub({
            'type': RedisPubSub.MessageTypes.FILE_UPLOAD,
            'user_id': user_id,
            'total_bookmarks': total_bookmarks,
        })

    @staticmethod
    def finish_upload(user_id: int):
        RedisPubSub.pub({
            'type': RedisPubSub.MessageTypes.FINISH,
            'user_id': user_id,
        })

    @staticmethod
    def update_status(user_id, bookmark_id, status):
        RedisPubSub.pub({
            'type': RedisPubSub.MessageTypes.BOOKMARK_CHANGE,
            'user_id': user_id,
            'bookmark_id': bookmark_id,
            'status': status
        })
