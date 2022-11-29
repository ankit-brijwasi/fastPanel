from datetime import datetime

from jose import jwt
from jose.exceptions import JWTError, JWTClaimsError, ExpiredSignatureError
from fastapi import exceptions, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from fastpanel import settings
from fastpanel.utils import timezone


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str):
    return pwd_context.hash(password)


def create_access_token(data: dict, expiry: datetime):
    to_encode = data.copy()
    to_encode.update({"exp": expiry})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_CONF["ALGORITHM"])
    return encoded_jwt


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_CONF["ALGORITHM"]])
    except (JWTError, JWTClaimsError, ExpiredSignatureError):
        raise exceptions.HTTPException(
            401,
            "Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return payload


async def auth_required(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    return payload


async def logged_in_user(payload: dict = Depends(auth_required)):
    print(payload)
    return {"hello"}