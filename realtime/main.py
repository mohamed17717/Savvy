import asyncio

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from common.jwt_utils import JwtManager
from common.progress import ProgressSSE, UserProgressSingleton
from common.redis_utils import RedisPubSub

load_dotenv()

app = FastAPI()

# add CORS so our web page can connect to our api
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:8080",
        "https://itab1.netlify.app",
        "http://itab1.netlify.app",
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
        user_id = data["user_id"]
        user_progress = await UserProgressSingleton.get_or_create_instance(user_id)
        user_progress.change(data)

    asyncio.create_task(RedisPubSub.sub(callback))
