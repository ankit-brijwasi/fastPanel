from datetime import datetime, date
import json

from bson import ObjectId, Timestamp
from pydantic_core import PydanticUndefinedType
from ..conf.settings import InstalledApp


class FastPanelJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        if isinstance(o, Timestamp):
            return o.as_datetime().isoformat()
        if isinstance(o, PydanticUndefinedType):
            return None
        if isinstance(o, InstalledApp):
            return {
                "app_name": o.app_name,
                "models": [{"name": model.__name__} for model in o.models]
            }
        return json.JSONEncoder.default(self, o)
