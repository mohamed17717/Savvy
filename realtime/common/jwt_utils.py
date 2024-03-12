import os
import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from rest_framework.response import Response
from fastapi import Request, HTTPException


class JwtManager:
    SECRET_KEY = os.getenv('JWT_SECRET')
    ALGORITHM = os.getenv('JWT_ALGORITHM')
    COOKIE_NAME = os.getenv('JWT_COOKIE_NAME')
    ACCESS_TOKEN_EXPIRE_DAYS = 3

    class AuthPayload(BaseModel, extra='allow'):
        user_id: int
        exp: float = Field(default_factory=lambda: (
            datetime.utcnow() + timedelta(days=JwtManager.ACCESS_TOKEN_EXPIRE_DAYS)
        ).timestamp())

    @classmethod
    def create_access_token(cls, data: dict) -> str:
        auth_payload = cls.AuthPayload.model_validate(data)
        encoded_jwt = jwt.encode(
            auth_payload.model_dump(), cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        return encoded_jwt

    @classmethod
    def inject_cookie(cls, response: Response, data: dict) -> None:
        response.set_cookie(
            cls.COOKIE_NAME,
            cls.create_access_token(data),
            max_age=timedelta(days=cls.ACCESS_TOKEN_EXPIRE_DAYS),
            domain=None,
            path='/',
            secure=False or None,
            httponly=True,
            samesite='Lax',
        )

    @classmethod
    def decode_token(cls, token) -> dict:
        data = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
        if data['exp'] < datetime.utcnow().timestamp():
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
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Signature expired")
        except jwt.DecodeError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))

        return cls.AuthPayload.model_validate(data)
