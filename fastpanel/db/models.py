from abc import ABC

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field
from pydantic._internal._model_construction import ModelMetaclass
from motor.motor_asyncio import AsyncIOMotorCollection

from .fields import PyObjectIdField


class MetaOptions:
    def __init__(
        self,
        parent,
        allowed_operations=None,
        search_fields=None,
        filter_fields=None,
        indexes=None,
        refer_to= "Self",
        hidden_fields=None,
        **options
    ):
        self.parent = parent
        self.allowed_operations = allowed_operations or ["get", "post", "update", "delete"]
        self.filter_fields = filter_fields or []
        self.indexes = indexes or []
        self.refer_to = refer_to or "Self"
        self.hidden_fields = hidden_fields or []
        self.search_fields = search_fields or ["_id"]
    
    def __repr__(self) -> str:
        return "<MetaOptions parent='%s'>" % (self.parent)


class MetaModel(ModelMetaclass):
    def __new__(cls, name, bases, attrs):
        meta_class = attrs.get('Meta', None)
        options = vars(meta_class) if meta_class else {}
        meta_options = MetaOptions(parent=name, **options)
        attrs['_meta'] = meta_options
        return super().__new__(cls, name, bases, attrs)


class Model(ABC, BaseModel, metaclass=MetaModel):
    """
    A Model helps you to reperesent your database entries as
    a python object. Once the settings are loaded, a reference
    for database connection is attached to Model 
    """

    id: PyObjectIdField = Field(
        alias="_id",
        default_factory=lambda: ObjectId(),
        json_schema_extra={
            "bsonType": "objectId",
            "description": "'_id' must be an objectId for representing a object"
        }
    )

    @classmethod
    def _construct_field_info(cls, field_name, value):
        desc = "'%s' must be an '%s'" % (field_name, value["bsonType"])
        if "description" in value: desc = value["description"]

        if value["bsonType"] in ["object", "array"]:
            return dict(
                bsonType=value["bsonType"],
                properties=value["properties"],
                description=desc
            )
        return dict(bsonType=value["bsonType"], description=desc)

    @classmethod
    def _get_bson_properties(cls, properties: dict):
        return {
            field: cls._construct_field_info(field, value) \
            for field, value in properties.items() \
            if not field == "_id"
        }

    @classmethod
    def get_collection_name(cls):
        if cls._meta.default.refer_to != "Self":
            return cls._meta.default.refer_to
        return cls.__name__.lower() + "s"

    @classmethod
    def get_bson_schema(cls) -> tuple:
        model_schema = cls.model_json_schema()
        schema = {
            "$jsonSchema": {
                "bsonType": "object",
                "title": model_schema["title"],
                "properties": cls._get_bson_properties(model_schema["properties"])
            }
        }
        if "required" in model_schema and len(model_schema["required"]) > 0:
            schema["$jsonSchema"]["required"] = model_schema["required"]

        return cls.get_collection_name(), schema

    @classmethod
    def get_model_name(cls):
        return cls.__name__
    
    @classmethod
    def get_collection(cls) -> AsyncIOMotorCollection:
        """
        Get the mongodb collection attached with this model
        raises error `SettingsNotLoaded` if called before loading settings
        """
        from ..conf import settings
        from ..exceptions import SettingsNotLoaded

        if not settings.SETTINGS_LOADED: raise SettingsNotLoaded
        return cls._conn[settings.DATABASE.get("name")][cls.get_collection_name()]

    def model_dump_json(self, dump_all: bool = False, *args, **kwargs) -> str:
        excluded_fields = kwargs.pop("exclude", []) or []
        if dump_all: excluded_fields = None
        else: excluded_fields.extend(self._meta.hidden_fields)
        return super().model_dump_json(*args, **kwargs, exclude=excluded_fields)

    def model_dump(self, dump_all: bool = False, *args, **kwargs) -> str:
        excluded_fields = kwargs.pop("exclude", []) or []
        if dump_all: excluded_fields = None
        else: excluded_fields.extend(self._meta.hidden_fields)
        return super().model_dump(*args, **kwargs, exclude=excluded_fields)

    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    def __str__(self) -> str:
        return f"<{self.get_model_name()} id='{self.id}'>"
