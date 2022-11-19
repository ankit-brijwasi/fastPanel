from datetime import datetime
from pydantic import EmailStr

from fastpanel.utils import timezone
from fastpanel.db.base_model import Model


class FastPanelUser(Model):
    """
    This model is used for authentication of users
    on fastPanel.
    """

    username: str
    password: str
    email: EmailStr
    first_name: str
    last_name: str
    date_joined: datetime = timezone.now()
    last_login: datetime = None
    is_active: bool = True

