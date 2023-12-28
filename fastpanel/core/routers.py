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
from pymongo import ReturnDocument

from . import schemas
from .auth.utils import auth_required
from ..core.serializers import FastPanelJSONEncoder
from ..conf import settings
from ..db.models import Model
from ..db.utils import get_model


router = APIRouter()


@router.get("/fetch-models")
def fetch_models(
        app_name: Optional[str] = None,
        # _ = Depends(auth_required),
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
    # _ = Depends(auth_required)
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
    # _ = Depends(auth_required)
):
    if not model:
        raise exceptions.HTTPException(status.HTTP_404_NOT_FOUND, "Model not found")

    if "get" not in Model._meta.default.allowed_operations:
        raise exceptions.HTTPException(status.HTTP_403_FORBIDDEN, "Permission denied")

    return model.model_json_schema()


@router.get("/models/objects/{object_id}")
async def retrieve_object(
    object_id: str, model: Model = Depends(get_model),
    # _ = Depends(auth_required),
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
        # _ = Depends(auth_required),
    ):
    model = get_model(payload.app, payload.model)
    if not model:
        raise exceptions.HTTPException(status.HTTP_404_NOT_FOUND, "Model not found")

    if "post" not in Model._meta.default.allowed_operations:
        raise exceptions.HTTPException(status.HTTP_403_FORBIDDEN, "Permission denied")

    model_obj: Model = model(**payload.data)
    collection = model.get_collection()

    try:
        dumped_data = model_obj.model_dump(dump_all=True)
        dumped_data["_id"] = dumped_data["id"]
        del dumped_data["id"]
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
    return model_obj


@router.patch("/models/objects/{object_id}", response_model=schemas.UpdateObject)
async def update_object(
        object_id: str,
        payload: schemas.UpdateObject,
        # _ = Depends(auth_required),
    ):
    model = get_model(payload.app, payload.model)
    if not model:
        raise exceptions.HTTPException(status.HTTP_404_NOT_FOUND, "Model not found")

    if "update" not in Model._meta.default.allowed_operations:
        raise exceptions.HTTPException(status.HTTP_403_FORBIDDEN, "Permission denied")
    
    if not ObjectId.is_valid(object_id):
        raise exceptions.HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid object id")

    collection = model.get_collection()

    try:
        updated_document = await collection.find_one_and_update(
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


    if not updated_document:
        raise exceptions.HTTPException(status.HTTP_404_NOT_FOUND, "Object not found")
    
    return {**payload.model_dump(), "data": model(**updated_document).model_dump()}


@router.delete("/models/objects/{object_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_object(
        object_id: str,
        model:Model = Depends(get_model),
        # _ = Depends(auth_required)
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
        # _ = Depends(auth_required)
    ):
    if not model:
        raise exceptions.HTTPException(status.HTTP_404_NOT_FOUND, "Model not found")

    if "get" not in Model._meta.default.allowed_operations:
        raise exceptions.HTTPException(status.HTTP_403_FORBIDDEN, "Permission denied")
    
    return list(model._meta.default.search_fields)


@router.post("/models/objects/search")
async def search(
        payload: schemas.SearchObject,
        # _ = Depends(auth_required)
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
