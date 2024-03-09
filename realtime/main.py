import asyncio

from fastapi import FastAPI

from common.redis_utils import RedisPubSub
from common.progress import UserProgressSingleton as UserProgress

from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
global_data = {'messages': [], 'progress': None}


@app.get("/")
async def index():
    print('endpoint hit')
    return {"message": "Hello, World!", **global_data}


@app.on_event("startup")
async def startup_event():
    async def callback(data: dict):
        user_id = data['user_id']
        user_progress = await UserProgress.get_instance(user_id)
        user_progress.change(data)

        global_data['messages'].append(data)
        global_data['progress'] = str(user_progress)

    asyncio.create_task(RedisPubSub.sub(callback))
