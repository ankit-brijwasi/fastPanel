from datetime import datetime
from pydantic import BaseModel
from fastpanel.db.models import PyObjectIdField


class UserCreate(BaseModel):
    username: str


class EventCreate(BaseModel):
    name: str
    level: int
    language: str
    admin_user: PyObjectIdField


class SubmitSolution(BaseModel):
    class ProposedAnswer(BaseModel):
        script: str
        started_on: str
        ended_on: str

    participant_id: str
    proposed_answer: ProposedAnswer