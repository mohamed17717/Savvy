import asyncio

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from common.redis_utils import RedisPubSub
from common.jwt_utils import JwtManager
from common.progress import UserProgressSingleton, ProgressSSE

from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# add CORS so our web page can connect to our api
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:8080"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/progress")
async def progress(request: Request):
    user_id = JwtManager.fastapi_auth(request).user_id
    user_progress = await UserProgressSingleton.get_instance(user_id)
    if user_progress is None:
        raise HTTPException(status_code=404, detail="User progress not found")

    return await ProgressSSE(user_progress).stream(request)


@app.on_event("startup")
async def startup_event():
    async def callback(data: dict):
        user_id = data['user_id']
        user_progress = await UserProgressSingleton.get_or_create_instance(user_id)
        user_progress.change(data)

    asyncio.create_task(RedisPubSub.sub(callback))
