import os
import redis
import json
from redis import asyncio as aioredis

from pydantic import BaseModel, Field


class RedisPubSub:
    CHANNEL_NAME = os.getenv('PUB_SUB_CHANNEL_NAME')
    REDIS_URL = os.getenv('REDIS_URL')

    clients = {
        'sync': redis.from_url(REDIS_URL),
        'async': aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
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
