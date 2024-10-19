import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, Request
from pydantic import BaseModel, Field
from rest_framework.response import Response


class JwtManager:
    SECRET_KEY = os.getenv("JWT_SECRET")
    ALGORITHM = os.getenv("JWT_ALGORITHM")
    COOKIE_NAME = os.getenv("JWT_COOKIE_NAME")
    ACCESS_TOKEN_EXPIRE_DAYS = 3

    class AuthPayload(BaseModel, extra="allow"):
        user_id: int
        exp: float = Field(
            default_factory=lambda: (
                datetime.utcnow() + timedelta(days=JwtManager.ACCESS_TOKEN_EXPIRE_DAYS)
            ).timestamp()
        )

    @classmethod
    def create_access_token(cls, data: dict) -> str:
        auth_payload = cls.AuthPayload.model_validate(data)
        return jwt.encode(
            auth_payload.model_dump(), cls.SECRET_KEY, algorithm=cls.ALGORITHM
        )

    @classmethod
    def inject_cookie(cls, response: Response, data: dict) -> None:
        response.set_cookie(
            cls.COOKIE_NAME,
            cls.create_access_token(data),
            max_age=timedelta(days=cls.ACCESS_TOKEN_EXPIRE_DAYS),
            domain=None,
            path="/",
            secure=False or None,
            httponly=True,
            samesite="Lax",
        )

    @classmethod
    def remove_cookie(cls, response: Response) -> None:
        response.delete_cookie(cls.COOKIE_NAME)

    @classmethod
    def decode_token(cls, token) -> dict:
        data = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
        if data["exp"] < datetime.now(timezone.utc).timestamp():
            raise jwt.ExpiredSignatureError

        return data

    @classmethod
    def fastapi_cookie(cls, request: Request, raise_exception=True) -> str:
        cookie = request.cookies.get(cls.COOKIE_NAME)
        if cookie is None and raise_exception:
            raise jwt.InvalidTokenError
        return cookie

    @classmethod
    def fastapi_auth(cls, request: Request) -> AuthPayload:
        try:
            token = cls.fastapi_cookie(request)
            data = cls.decode_token(token)
        except jwt.ExpiredSignatureError as e:
            raise HTTPException(status_code=401, detail="Signature expired") from e
        except jwt.DecodeError as e:
            raise HTTPException(status_code=401, detail="Invalid token") from e
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail="Invalid token") from e
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e)) from e

        return cls.AuthPayload.model_validate(data)
