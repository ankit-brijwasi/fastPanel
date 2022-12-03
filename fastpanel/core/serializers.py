from datetime import datetime, date
import json
from bson import ObjectId, Timestamp


class FastPanelJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        if isinstance(o, Timestamp):
            return o.as_datetime().isoformat()
        return json.JSONEncoder.default(self, o)
