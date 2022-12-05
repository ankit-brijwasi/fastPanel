import json
from typing import List, Dict

from bson import ObjectId
from fastapi.exceptions import HTTPException
from motor.core import Collection
from pydantic import BaseModel, Field
from pymongo import errors

from fastpanel.core.serializers import FastPanelJSONEncoder


class PyObjectIdField(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class Model(BaseModel):
    id: PyObjectIdField = Field(default_factory=PyObjectIdField, alias="_id")

    @classmethod
    def get_collection_name(cls):
        return cls.__name__.lower() + "s"
    
    async def save(self, db) -> dict:
        collection: Collection = db[self.get_collection_name()]

        try:
            added_obj = await collection.insert_one(self.dict())
            fetch_obj = await collection.find_one({ "_id": added_obj.inserted_id })
        except errors.DuplicateKeyError as e:
            raise HTTPException(400, e.details["errmsg"])
        except Exception as e:
            raise HTTPException(500, f"error: {e}")

        return fetch_obj

    async def fetch_mongo_field(self, field_value, coll_name):
        collection: Collection = self._mongo_db[coll_name]
        fetched_info = await collection.find_one({ "_id": ObjectId(field_value)})
        if fetched_info:
            if fetched_info.get("id"): del fetched_info["id"]
        return fetched_info

    async def transform_data(self, fields_to_transform: List[Dict]):
        data = self.dict()
        if hasattr(self, "_mongo_db"):
            for field in fields_to_transform:
                try:
                    value = getattr(self, field.get("field_name"))
                    coll_name = field.get("model", self.get_collection_name()).get_collection_name()
                    data[field.get("field_name")] = await self.fetch_mongo_field(value, coll_name)
                except KeyError:
                    raise ValueError("unable to find field: %s on collection %s" % (field, self.get_collection_name()))
            
        return json.loads(json.dumps(data, cls=FastPanelJSONEncoder))

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
        arbitrary_types_allowed = True

    class Meta:
        def __init__(
            self,
            allowed_operations: str = ["get", "post", "update", "delete"],
            search_fields = ["_id"],
            filter_fields = []
        ) -> None:
            self.allowed_operations = allowed_operations
            self.search_fields = search_fields
            self.filter_fields = filter_fields

    _meta = Meta()