from datetime import datetime
from typing import Optional

from pydantic import Field, EmailStr, field_validator

from ...db.models import Model
from ...utils import timezone


class FastPanelUser(Model):
    username: str = Field(
        json_schema_extra={
            "bsonType": "string",
            "description": "'username' must be a string and is required"
        }
    )
    password: str = Field(
        json_schema_extra={
            "bsonType": "string",
            "description": "'password' must be a string and is required"
        }
    )
    email: Optional[EmailStr] = Field(
        json_schema_extra={
            "bsonType": ["string", "null"],
            "description": "'email' must be a string"
        },
        default=None
    )
    first_name: Optional[str] = Field(
        json_schema_extra={
            "bsonType": ["string", "null"],
            "description": "'first_name' must be a string"
        },
        default=None
    )
    last_name: Optional[str] = Field(
        json_schema_extra={
            "bsonType": ["string", "null"],
            "description": "'last_name' must be a string"
        },
        default=None
    )
    date_joined: Optional[datetime] = Field(
        json_schema_extra={
            "bsonType": "date",
            "description": "'date_joined' must be a date"
        },
        default=timezone.now(),
        frozen=True
    )
    last_login: Optional[datetime] = Field(
        json_schema_extra={
            "bsonType": ["date", "null"],
            "description": "'last_login' must be a date if it is passed"
        },
        default=None
    )
    is_active: bool = Field(
        json_schema_extra={
            "bsonType": "bool",
            "description": "'is_active' must be a boolean"
        },
        default=True
    )

    @field_validator("password")
    @classmethod
    def make_password(cls, password: str) -> str:
        if password.startswith("fpanel_hash_"):
            return password
        else:
            from ..auth.utils import get_password_hash
            return get_password_hash(password)

    class Meta:
        indexes = [
            {"keys": "username", "unique": True},
            {"keys": "email", "unique": True, "partialFilterExpression": {"email": {"$type": "string"}}}
        ]
        hidden_fields = ["password"]
        search_fields = ["_id", "username", "email", "first_name", "last_name"]
