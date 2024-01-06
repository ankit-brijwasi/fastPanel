from typing import Literal, Type
from pydantic import Field, validate_call
from .models import Model


@validate_call
def EmbdedField(
        related_to: Type[Model],
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

    if embeding_type == "many-to-many":
        return Field(
            *args,
            **kwargs,
            json_schema_extra={
                "bsonType": "array",
                "relation_type": "embeded",
                "related_to": related_to.get_collection_name()
            }
        )

    return Field(
        *args,
        **kwargs,
        json_schema_extra={
            "bsonType": "object",
            "relation_type": "embeded",
            "related_to": related_to.get_collection_name()
        }
    )
