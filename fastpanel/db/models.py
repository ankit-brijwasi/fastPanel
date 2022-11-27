from fastapi.exceptions import HTTPException
from motor.core import Collection
from pydantic import BaseModel, Field

from bson import ObjectId
from pymongo import errors


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

    class Config:
        allow_population_by_field_name = True
        # arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        # validate_assignment = True

model = Model