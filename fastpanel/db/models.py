from abc import ABC

import jsonschema
from pydantic import BaseModel, ConfigDict, Field
from pydantic._internal._model_construction import ModelMetaclass
from motor.motor_asyncio import AsyncIOMotorCollection

from .fields import PyObjectIdField, ObjectId


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
        is_nested=False,
        **options
    ):
        self.parent = parent
        self.allowed_operations = allowed_operations or ["get", "post", "update", "delete"]
        self.filter_fields = filter_fields or []
        self.indexes = indexes or []
        self.refer_to = refer_to or "Self"
        self.hidden_fields = hidden_fields or []
        self.search_fields = search_fields or ["_id"]
        self.is_nested = is_nested
    
    def __repr__(self) -> str:
        return "<MetaOptions parent='%s' is_nested='%s'>" % (self.parent, self.is_nested)


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
    def get_collection_name(cls):
        if cls._meta.default.refer_to != "Self":
            return cls._meta.default.refer_to
        return cls.__name__.lower() + "s"

    @classmethod
    def _get_model_attrs(cls, raw_schema: dict, is_internal=True):
        default_description = lambda field_name, type: "\'%s\' must be an \'%s\'" % (field_name, type)
        resolver = jsonschema.RefResolver.from_schema(raw_schema)
        attrs = {}
        schema = {"bsonType": "object", "title": raw_schema["title"].strip()}

        if "required" in raw_schema and len(raw_schema["required"]) > 0:
            schema["required"] = raw_schema["required"]
        if "title" in raw_schema:
            schema["title"] = raw_schema["title"]

        for key, value in raw_schema["properties"].items():
            if value["bsonType"] == "array":
                assert \
                    not ("anyOf" in value["items"] or "allOf" in value["items"]),\
                    "Multiple values for array are not supported yet."

                resolved_ref = resolver.resolve(value["items"]["$ref"])[1]
                attrs[key] = {
                    "bsonType": value["bsonType"],
                    "title": value["title"].strip(),
                    "description": value.get(
                        "description",
                        default_description(key, value["bsonType"])
                    ),
                    "items": cls._get_model_attrs(resolved_ref, is_internal)
                }
            elif value["bsonType"] == "object":
                assert \
                    not (
                        0 <= len(value.get("allOf", [])) > 1 or
                        0 <= len(value.get("anyOf", [])) > 1
                    ),\
                    "Multiple values for objects are not supported yet."
                
                ref_field = None
                if "allOf" in value:
                    ref_field = value.pop("allOf")
                elif "anyOf" in value:
                    ref_field = value.pop("anyOf")

                resolved_ref = resolver.resolve(ref_field[0]["$ref"])[1]
                attrs[key] = {
                    **cls._get_model_attrs(resolved_ref, is_internal),
                    "description": value.get(
                        "description",
                        default_description(key, value["bsonType"])
                    )
                }
            else:
                attrs[key] = {
                    "bsonType": value["bsonType"],
                    "title": value["title"].strip(),
                    "description": value.get(
                        "description",
                        default_description(key, value["bsonType"])
                    ),
                }

            if not is_internal:
                fields_needed = ["relation_type", "format", "type", "anyOf", "allOf", "title"]
                for field in set(fields_needed).intersection(value):
                    attrs[key][field] = value[field]

        schema["properties"] = attrs
        return schema

    @classmethod
    def get_bson_schema(cls) -> tuple:
        model_schema = cls.model_json_schema()
        return (
            cls.get_collection_name(),
            {"$jsonSchema": cls._get_model_attrs(model_schema)}
        )

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

    @classmethod
    def dump_model_attributes(cls):
        model_schema = cls.model_json_schema()
        return cls._get_model_attrs(model_schema, False)

    def _get_excluded_fields(self, dump_all, fields):
        if dump_all: return None
        excluded_fields = fields.pop("exclude", []) or []
        excluded_fields.extend(self._meta.hidden_fields)
        return excluded_fields

    def model_dump_json(self, dump_all: bool = False, by_alias: bool = True, *args, **kwargs) -> str:
        excluded_fields = self._get_excluded_fields(dump_all, kwargs)
        return super().model_dump_json(by_alias=by_alias, *args, **kwargs, exclude=excluded_fields)

    def model_dump(self, dump_all: bool = False, by_alias: bool = True, *args, **kwargs) -> str:
        excluded_fields = self._get_excluded_fields(dump_all, kwargs)
        return super().model_dump(by_alias=by_alias, *args, **kwargs, exclude=excluded_fields)

    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    def __str__(self) -> str:
        return f"<{self.get_model_name()} id='{self.id}'>"
