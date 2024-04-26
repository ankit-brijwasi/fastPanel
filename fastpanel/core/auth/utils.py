from datetime import datetime, timedelta
from typing import Union
import json

from bson import ObjectId
from fastapi import exceptions, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jose.exceptions import JWTError, JWTClaimsError, ExpiredSignatureError
from passlib.context import CryptContext

from ..accounts import FastPanelUser
from ...conf import settings
from ...utils import timezone


oauth2_scheme = lambda: OAuth2PasswordBearer(tokenUrl=f"/fastpanel/auth/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password.strip("fpanel_hash_"))


def get_password_hash(password: str):
    hashed_string = pwd_context.hash(password)
    return "fpanel_hash_" + hashed_string


def create_token(data: Union[str, dict], expiry: datetime):
    if type(data) == str: data = json.loads(data)
    to_encode = data.copy()
    to_encode.update({"exp": expiry})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def decode_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except (JWTError, JWTClaimsError, ExpiredSignatureError):
        raise exceptions.HTTPException(
            401,
            "Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return payload


def create_new_access_token(refresh_token: str):
    payload = decode_token(refresh_token)
    access_expiry = timezone.now() + timedelta(seconds=settings.ACCESS_TOKEN_EXPIRATION)
    return create_token(payload, access_expiry)


async def auth_required(token: str = Depends(oauth2_scheme(), use_cache=False)):
    payload = decode_token(token)
    return payload


async def logged_in_user(req: Request, payload: dict = Depends(auth_required)):
    collection = FastPanelUser.get_collection()
    fetched_user = await collection.find_one({"_id": ObjectId(payload["user_id"])})
    user = FastPanelUser(**fetched_user)
    if not user.is_active: raise exceptions.HTTPException(403, "User is inactive")
    return user


def create_auth_tokens(user: FastPanelUser):
    """
    Creates access and refresh token
    """
    access_expiry = timezone.now() + timedelta(seconds=settings.ACCESS_TOKEN_EXPIRATION)
    refresh_expiry = timezone.now() + timedelta(seconds=settings.REFRESH_TOKEN_EXPIRATION)

    access_token = create_token(user.model_dump_json(), access_expiry)
    refresh_token = create_token(user.model_dump_json(), refresh_expiry)
    return {"access_token": access_token, "refresh_token": refresh_token}