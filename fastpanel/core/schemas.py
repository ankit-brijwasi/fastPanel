from datetime import datetime
from typing import Optional, List

from bson import ObjectId
from fastapi.exceptions import HTTPException
from fastapi_pagination import Page
from motor.core import Collection
from pydantic import BaseModel, EmailStr, Field, validator
from pymongo import errors

from fastpanel.db.models import Model
from fastpanel.utils import timezone
from fastpanel.utils.auth import get_password_hash


class FastPanelUser(Model):
    """
    This model is used for authentication of users
    on fastPanel.
    """

    username: str
    password: str = Field(exclude=True)
    email: Optional[EmailStr]
    first_name: Optional[str]
    last_name: Optional[str]
    date_joined: datetime = timezone.now()
    last_login: datetime = None
    is_active: bool = True

    @validator("date_joined")
    @classmethod
    def set_date_joined(cls, date_joined):
        return date_joined or timezone.now()

    @validator("last_login")
    @classmethod
    def set_last_login(cls, last_login):
        return last_login or None

    @validator("is_active")
    @classmethod
    def set_is_active(cls, is_active):
        if is_active == None:
            return True
        return is_active
    
    async def save(self, db) -> dict:
        try:
            collection: Collection = db[self.get_collection_name()]
            added_obj = await collection.insert_one(
                {
                    **self.dict(),
                    "password": get_password_hash(self.password)
                }
            )
            fetch_obj = await collection.find_one({ "_id": added_obj.inserted_id })
            return fetch_obj
    
        except errors.DuplicateKeyError as e:
            raise HTTPException(400, e.details["errmsg"])
        except Exception as e:
            raise HTTPException(500, f"error: {e}")


class FastPanelUserCreate(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class LoginRes(BaseModel):
    access_token: str
    user: dict

    class Config:
        json_encoders = {ObjectId: str}


class FetchModelRes(BaseModel):
    class Model(BaseModel):
        name: str
        import_path: str

    name: str
    base_path: str
    models: List[Model]


class CustomPage(Page):
    class Config:
        json_encoders = {ObjectId: str}


class CreateObject(BaseModel):
    data: dict
    app_name: str
    model_name: str

    class Config:
        json_encoders = {ObjectId: str}


class UpdateObject(BaseModel):
    object_id: str
    data: dict
    app_name: str
    model_name: str

    class Config:
        json_encoders = {ObjectId: str}


class DeleteObject(BaseModel):
    object_id: str
    app_name: str
    model_name: str

    class Config:
        json_encoders = {ObjectId: str}
