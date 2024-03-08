from fastapi import FastAPI
import asyncio
from redis import asyncio as aioredis


app = FastAPI()
data = {'count': 0, 'messages': []}


@app.get("/")
async def index():
    print('endpoint hit')
    return {"message": "Hello, World!", **data}


async def redis_listener(channel_name: str):
    print('[main]: task `bookmarks_progress` started ...')
    redis_client = aioredis.from_url(
        'redis://redis:6379', encoding="utf-8", decode_responses=True)

    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel_name)
    while True:
        data['count'] += 1
        message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
        if message:
            data['messages'].append(message)
            print(f"Received message: {message}")
        else:
            print("No message received")


@app.on_event("startup")
async def startup_event():
    print("startup event")
    asyncio.create_task(redis_listener('bookmarks_progress'))
