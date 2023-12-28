from typing import Any, Literal

from bson import ObjectId
from pydantic_core import core_schema
from typing_extensions import Annotated

from pydantic import GetJsonSchemaHandler, Field
from pydantic.json_schema import JsonSchemaValue
    

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
        embeding_type: Literal['one-to-one', 'many-to-one'] = "one-to-one",
        *args,
        **kwargs
    ):
    """
    Use this field to embed a document of another collection into this collection.
    :param related_to: The model with which this field is being embded to
    :param embeding_type: one-to-one or many-to-many
    """
    if embeding_type == "one-to-one":
        _, schema = related_to.get_bson_schema()
    elif embeding_type == "many-to-many":
        schema = {}
    else:
        raise ValueError("Invalid value for '%s' passed" % (embeding_type))

    return Field(
        *args,
        **kwargs,
        json_schema_extra=schema.get("$jsonSchema")
    )


# def RefrencedField(related_to, related_via: str, *args, **kwargs):
#     return Field(*args, **kwargs)
