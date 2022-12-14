from typing import Optional
from datetime import datetime

from fastapi.exceptions import HTTPException
from motor.core import Collection
from pydantic import EmailStr, Field, validator
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
    date_joined: datetime = Field(default=timezone.now(), editable=False)
    last_login: datetime = Field(default=None, editable=False)
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

    _meta = Model.Meta(
        search_fields=[
            "_id",
            "username",
            "email",
            "first_name",
            "last_name",
            "date_joined",
            "last_login"
        ],
        filter_fields=[
            {"field_name": "is_active", "type": "bool"}
        ]
    )
