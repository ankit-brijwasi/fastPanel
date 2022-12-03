from datetime import datetime

from bson import ObjectId
from fastapi.exceptions import HTTPException
from pydantic import Field, validator

from fastpanel.utils import timezone
from fastpanel.db import models


class Event(models.Model):
    name: str
    level: int
    language: str = Field(default="python")
    created_on: datetime = Field(default=timezone.now())

    @validator("level")
    @classmethod
    def validate_level(cls, level):
        if level not in (0, 1):
            raise HTTPException(400, f"invalid level: {level}")
        return level

    @validator("language")
    @classmethod
    def validate_language(cls, language):
        if language not in ("python", "javascript", "go", "c++"):
            raise HTTPException(400, f"language: {language} not supported right now")
        return language


class Participant(models.Model):
    name: str
    event: ObjectId