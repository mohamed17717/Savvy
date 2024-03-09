import os
import redis
import json
from redis import asyncio as aioredis


from pydantic import BaseModel, Extra, Field



class RedisPubSub:
    CHANNEL_NAME = os.getenv('PUB_SUB_CHANNEL_NAME')
    HOST = os.getenv('REDIS_HOST')
    PORT = os.getenv('REDIS_PORT')

    clients = {
        'sync': redis.Redis(host=HOST, port=PORT, db=0),
        'async': aioredis.from_url(f'redis://{HOST}:{PORT}', encoding="utf-8", decode_responses=True)
    }
    
    class MessageTypes:
        FILE_UPLOAD = 1
        BOOKMARK_CHANGE = 2

    class FileUploadData(BaseModel, extra=Extra.allow):
        user_id: int
        total_bookmarks: int
        type: int = Field(default_factory=lambda: RedisPubSub.MessageTypes.FILE_UPLOAD)

    class BookmarkChangeData(BaseModel, extra=Extra.allow):
        user_id: int
        bookmark_id: int
        status: int
        type: int = Field(default_factory=lambda: RedisPubSub.MessageTypes.BOOKMARK_CHANGE)

    @classmethod
    def __validate_data(cls, data: dict) -> dict:
        _type = data.get('type')
        if _type is None:
            raise ValueError('type is required')
        elif _type == cls.MessageTypes.FILE_UPLOAD:
            data = cls.FileUploadData(**data)
        elif _type == cls.MessageTypes.BOOKMARK_CHANGE:
            data = cls.BookmarkChangeData(**data)
        else:
            raise ValueError('invalid type')
        
        return data.dict()

    @classmethod
    def pub(cls, data: dict) -> None:
        data = cls.__validate_data(data)
        client = cls.clients['sync']
        client.publish(cls.CHANNEL_NAME, json.dumps(data))

    @classmethod
    async def sub(cls, callback, counter):
        client = cls.clients['async']
        pubsub = client.pubsub()
        await pubsub.subscribe(cls.CHANNEL_NAME)
        while True:
            counter()
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message['type'] == 'message':
                callback(json.loads(message['data']))
                print(f"Received message: {message}")

            
        
