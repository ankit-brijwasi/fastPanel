from pydantic import BaseModel

class CreateObject(BaseModel):
    data: dict
    app: str = "fastpanel.core.accounts"
    model: str = "FastPanelUser"


class UpdateObject(BaseModel):
    data: dict
    app: str = "fastpanel.core.accounts"
    model: str = "FastPanelUser"


class SearchObject(BaseModel):
    data: dict
    app: str = "fastpanel.core.accounts"
    model: str = "FastPanelUser"
