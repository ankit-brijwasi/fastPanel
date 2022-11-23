from datetime import datetime
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, EmailStr, Field

from fastpanel.utils import timezone


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class FastPanelUser(BaseModel):
    """
    This model is used for authentication of users
    on fastPanel.
    """

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    username: str
    password: str
    email: Optional[EmailStr]
    first_name: Optional[str]
    last_name: Optional[str]
    date_joined: datetime = timezone.now()
    last_login: datetime = None
    is_active: bool = True

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class FastPanelUserCreate(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class LoginRes(BaseModel):
    access_token: str
    user: FastPanelUser

    class Config:
        json_encoders = {ObjectId: str}
