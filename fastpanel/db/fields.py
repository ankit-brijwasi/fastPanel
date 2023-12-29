from typing import Any, Literal

from bson import ObjectId
from pydantic_core import core_schema
from pydantic import GetJsonSchemaHandler, Field
from pydantic.json_schema import JsonSchemaValue
from typing_extensions import Annotated


class _ObjectIdPydanticAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler
    ) -> core_schema.CoreSchema:
        def validate_from_str(input_value: str) -> ObjectId:
            return ObjectId(input_value)

        return core_schema.union_schema(
            [
                # check if it's an instance first before doing any further work
                core_schema.is_instance_schema(ObjectId),
                core_schema.no_info_plain_validator_function(validate_from_str),
            ],
            serialization=core_schema.to_string_ser_schema(),
        )
    
    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return handler(core_schema.str_schema())


PyObjectIdField = Annotated[ObjectId, _ObjectIdPydanticAnnotation]


def EmbdedField(
        related_to,
        embeding_type: Literal['one-to-many', 'many-to-many'] = "one-to-many",
        *args,
        **kwargs
    ):
    """
    Use this field to embed a document of another collection into this collection.
    :param related_to: The model with which this field is being embded to
    :param embeding_type: one-to-many or many-to-many
    """
    if not embeding_type in ["one-to-many", "many-to-many"]:
        raise ValueError("Invalid value for '%s' passed" % (embeding_type))

    schema: dict = related_to.get_bson_schema()[1]

    if "required" in schema["$jsonSchema"] and len(schema["$jsonSchema"].get("required")) > 0:
        schema["$jsonSchema"]["required"].append("_id")

    if embeding_type == "many-to-many":
        schema = {
            "bsonType": "array",
            "items": schema["$jsonSchema"],
            "relation_type": "embeded"
        }
        return Field(*args, **kwargs, json_schema_extra=schema)

    return Field(*args, **kwargs, json_schema_extra={**schema, "relation_type": "embeded"})