from typing import Optional, Any
from datetime import datetime

from fastapi.exceptions import HTTPException
from pydantic import Field, validator, BaseModel


from fastpanel.utils import timezone
from fastpanel.db import models


class User(models.Model):
    username: str

    @validator("username")
    @classmethod
    def validate_name(cls, username: str):
        return username.lower()

    async def save(self, db) -> dict:
        user = await db[self.get_collection_name()].find_one({ "username": self.username })
        if user: return user
        return await super().save(db)


class Question(models.Model):
    statement: str
    level: int = Field(default=0)
    language: str = Field(default="python3")
    expected_output: Any

    @validator("level")
    @classmethod
    def validate_level(cls, level):
        if level not in (0, 1):
            raise HTTPException(400, f"invalid level: {level}")
        return level
    
    @validator("language")
    @classmethod
    def validate_language(cls, language):
        if language not in ("python3", "nodejs", "c", "go", "cpp"):
            raise HTTPException(400, f"language: {language} not supported right now")
        return language


class Event(models.Model):
    name: str
    level: int
    language: str = Field(default="python3")
    created_on: datetime = Field(default=timezone.now())
    question_assigned: Optional[models.PyObjectIdField] = Field(connected_with="devduels.Question")
    admin_user: models.PyObjectIdField = Field(connected_with="devduels.User")
    has_started: bool = Field(default=False)

    @validator("level")
    @classmethod
    def validate_level(cls, level):
        if level not in (0, 1):
            raise HTTPException(400, f"invalid level: {level}")
        return level

    @validator("language")
    @classmethod
    def validate_language(cls, language):
        if language not in ("python3", "nodejs", "c", "go", "cpp"):
            raise HTTPException(400, f"language: {language} not supported right now")
        return language


class Participant(models.Model):
    class Solution(BaseModel):
        code: str
        output: Any
        output_time: str

    user: models.PyObjectIdField
    event: models.PyObjectIdField
    is_ready: bool = Field(default=False)
    solution: Optional[Solution]
    time_taken: Optional[str]
