from pydantic import BaseModel
from ..accounts.models import FastPanelUser


class LoginRes(BaseModel):
    access_token: str
    refresh_token: str
    user: FastPanelUser
