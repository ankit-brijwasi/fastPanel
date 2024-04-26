from typing import Optional
import json

from bson import ObjectId
from fastapi import (
    APIRouter,
    status,
    Response,
    exceptions,
    Depends,
)
from pydantic import ValidationError
from pymongo import ReturnDocument

from . import schemas
from .auth.utils import auth_required
from ..core.serializers import FastPanelJSONEncoder
from ..conf import settings
from ..db.models import Model
from ..db.utils import get_model


router = APIRouter()


@router.get("/fetch-apps")
def fetch_models(
        app_name: Optional[str] = None,
        _ = Depends(auth_required),
    ):
    apps = settings.INSTALLED_APPS
    if app_name:
        apps = list(filter(lambda x: x.app_name == app_name, apps))

    data = json.dumps(apps, cls=FastPanelJSONEncoder)
    return Response(
        content=data,
        status_code=status.HTTP_200_OK,
        headers={"Content-Type": "application/json"}
    )


@router.get("/models/objects/")
async def list_objects(
    model: Model = Depends(get_model),
    _ = Depends(auth_required)
):
    if not model:
        raise exceptions.HTTPException(status.HTTP_404_NOT_FOUND, "Model not found")

    if "get" not in model._meta.default.allowed_operations:
        raise exceptions.HTTPException(status.HTTP_403_FORBIDDEN, "Permission denied")

    collection = model.get_collection()
    cursor = collection.find().sort([('_id', 1)])
    return [model(**entry) for entry in await cursor.to_list(None)]


@router.get("/models/objects/attributes")
async def model_attributes(
    model: Model = Depends(get_model),
    _ = Depends(auth_required)
):
    if not model:
        raise exceptions.HTTPException(status.HTTP_404_NOT_FOUND, "Model not found")

    if "get" not in Model._meta.default.allowed_operations:
        raise exceptions.HTTPException(status.HTTP_403_FORBIDDEN, "Permission denied")

    return model.dump_model_attributes()


@router.get("/models/objects/{object_id}")
async def retrieve_object(
    object_id: str, model: Model = Depends(get_model),
    _ = Depends(auth_required),
):
    if not model:
        raise exceptions.HTTPException(status.HTTP_404_NOT_FOUND, "Model not found")

    if "get" not in model._meta.default.allowed_operations:
        raise exceptions.HTTPException(status.HTTP_403_FORBIDDEN, "Permission denied")

    collection = model.get_collection()

    try:
        db_obj = await collection.find_one({"_id": ObjectId(object_id)})
    except Exception as e:
        raise exceptions.HTTPException(500, f"error: {e}")
    
    if db_obj is None:
        raise exceptions.HTTPException(404, "Object not found")
    
    return model(**db_obj)


@router.post("/models/objects/")
async def create_objects(
        payload: schemas.CreateObject,
        _ = Depends(auth_required),
    ):
    model = get_model(payload.app, payload.model)
    if not model:
        raise exceptions.HTTPException(status.HTTP_404_NOT_FOUND, "Model not found")

    if "post" not in Model._meta.default.allowed_operations:
        raise exceptions.HTTPException(status.HTTP_403_FORBIDDEN, "Permission denied")

    # TODO: Commenting for now, will turn on this check after proper testing
    # if model._meta.default.is_nested:
    #     raise exceptions.HTTPException(status.HTTP_403_FORBIDDEN, "Model is nested! Permission deined")

    try:
        model_obj: Model = model(**payload.data)
    except ValidationError as e:
        raise exceptions.HTTPException(422, {"count": e.error_count(), "errors": e.errors()})
    collection = model.get_collection()

    try:
        dumped_data = model_obj.model_dump(dump_all=True)
        await collection.insert_one(dumped_data)
    except Exception as e:
        raise exceptions.HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "msg": "Unable to insert data to db!",
                "error": str(e),
                "code": e.code if hasattr(e, "code") else None
            }
        )
    return model(**dumped_data)


@router.patch("/models/objects/{object_id}")
async def update_object(
        object_id: str,
        payload: schemas.UpdateObject,
        _ = Depends(auth_required),
    ):
    model = get_model(payload.app, payload.model)
    if not model:
        raise exceptions.HTTPException(status.HTTP_404_NOT_FOUND, "Model not found")

    if "update" not in Model._meta.default.allowed_operations:
        raise exceptions.HTTPException(status.HTTP_403_FORBIDDEN, "Permission denied")

    collection = model.get_collection()

    try:
        document = await collection.find_one({"_id": ObjectId(object_id)})
        if not document:
            raise exceptions.HTTPException(
                status.HTTP_404_NOT_FOUND,
                "Object not found"
            )

        try:
            document = model(**document)
        except ValidationError as e:
            raise exceptions.HTTPException(422, {"count": e.error_count(), "errors": e.errors()})

        for field_name in set(document.model_dump(True).keys()).intersection(payload.data.keys()):
            setattr(document, field_name, payload.data[field_name])

        document = await collection.find_one_and_update(
            {"_id": ObjectId(object_id)},
            {"$set": payload.data},
            return_document=ReturnDocument.AFTER
        )
    except Exception as e:
        raise exceptions.HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "msg": "Unable to update the object!",
                "error": str(e),
                "code": e.code if hasattr(e, "code") else None
            }
        )
    return model(**document)


@router.delete("/models/objects/{object_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_object(
        object_id: str,
        model:Model = Depends(get_model),
        _ = Depends(auth_required)
    ):
    if not model:
        raise exceptions.HTTPException(status.HTTP_404_NOT_FOUND, "Model not found")

    if "delete" not in Model._meta.default.allowed_operations:
        raise exceptions.HTTPException(status.HTTP_403_FORBIDDEN, "Permission denied")
    
    if not ObjectId.is_valid(object_id):
        raise exceptions.HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid object id")

    collection = model.get_collection()

    try:
        db_collection = await collection.find_one_and_delete(
            {"_id": ObjectId(object_id)}
        )
    except Exception as e:
        raise exceptions.HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "msg": "Unable to delete the object!",
                "error": str(e),
                "code": e.code if hasattr(e, "code") else None
            }
        )

    if db_collection is None:
        raise exceptions.HTTPException(404, "Object not found")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/models/objects/search/fields")
async def get_search_fields(
        model: Model = Depends(get_model),
        _ = Depends(auth_required)
    ):
    if not model:
        raise exceptions.HTTPException(status.HTTP_404_NOT_FOUND, "Model not found")

    if "get" not in Model._meta.default.allowed_operations:
        raise exceptions.HTTPException(status.HTTP_403_FORBIDDEN, "Permission denied")
    
    return list(model._meta.default.search_fields)


@router.post("/models/objects/search")
async def search(
        payload: schemas.SearchObject,
        _ = Depends(auth_required)
    ):
    model: Model = get_model(payload.app, payload.model)
    if not model:
        raise exceptions.HTTPException(status.HTTP_404_NOT_FOUND, "Model not found")

    if "get" not in Model._meta.default.allowed_operations:
        raise exceptions.HTTPException(status.HTTP_403_FORBIDDEN, "Permission denied")

    collection = model.get_collection()

    try:
        cursor = collection.find({**payload.data}).sort([("_id", 1)])
    except Exception as e:
        raise exceptions.HTTPException(500, f"error: {e}")

    return [Model(**entry) for entry in await cursor.to_list(None)]
