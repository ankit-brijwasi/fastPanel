from typing import Optional, List

from bson import ObjectId
from fastapi_pagination import Page
from pydantic import BaseModel, EmailStr


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
