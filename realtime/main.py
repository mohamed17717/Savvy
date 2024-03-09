import asyncio

from fastapi import FastAPI

from common.redis_utils import RedisPubSub
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
data = {'count': 0, 'messages': []}


@app.get("/")
async def index():
    print('endpoint hit')
    return {"message": "Hello, World!", **data}


@app.on_event("startup")
async def startup_event():
    def callback(message):
        print(f"Received message: {message}")
        data['messages'].append(message)
        data['count'] += 1

    asyncio.create_task(RedisPubSub.sub(callback))
