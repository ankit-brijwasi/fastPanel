from datetime import timedelta
from typing import Optional

from bson.json_util import ObjectId
from fastapi import APIRouter, Depends, Request, Response, exceptions, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi_pagination import Page, add_pagination, paginate

from motor.core import Collection
from pymongo import ReturnDocument
from pymongo import errors

from .schemas import (
    LoginRes,
    FetchModelRes,
    CustomPage,
    CreateObject,
    UpdateObject,
    DeleteObject
)
from .models import FastPanelUser
from ..utils.auth import create_access_token, verify_password, logged_in_user
from ..utils.helpers import get_model
from ..utils import timezone
from fastpanel import settings
from fastpanel.db import models
from fastpanel.utils.helpers import collect_models, get_app_models


router = APIRouter()
router.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/login", response_model=LoginRes)
async def login(req: Request, response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    error =  exceptions.HTTPException(400, "Incorrect username or password")

    collection: Collection = req.app.db["fastpanelusers"]
    db_user = await collection.find_one({"username": form_data.username})
    if not db_user: raise error

    user = FastPanelUser(**db_user)
    if not verify_password(form_data.password, user.password): raise error

    if not user.is_active: raise exceptions.HTTPException(403, "This user is inactive")

    expiry = timezone.now() + settings.JWT_CONF.get("ACCESS_TOKEN_EXPIRY", timedelta(minutes=15))
    access_token = create_access_token({"user_id": str(user.id)}, expiry)
    expiry_in_sec = int(expiry.timestamp())
    response.set_cookie(
        "_SID",
        access_token,
        max_age=expiry_in_sec,
        expires=expiry_in_sec,
        httponly=True,
        secure=True
    )
    db_user = await collection.find_one_and_update(
        {"_id": user.id},
        {"$set": {"last_login": timezone.now()}},
        return_document=ReturnDocument.AFTER
    )
    return {"access_token": access_token, "user": FastPanelUser(**db_user)}


@router.get("/fetch-models", response_model=Page[FetchModelRes])
async def fetch_models(user: dict = Depends(logged_in_user), app_name: Optional[str] = None):
    models = collect_models(settings.CONFIG_FILE_PATH)
    if app_name: models = get_app_models(app_name, models)
    return paginate(models)


@router.get("/models/objects/", response_model=CustomPage)
async def list_objects(req: Request, app_name: str, model_name: str):
    Model: models.Model = get_model(app_name, model_name)
    if "get" not in Model.Meta.allowed_operations:
        raise exceptions.HTTPException(status.HTTP_403_FORBIDDEN, "Permission denied")

    collection: Collection = req.app.db[Model.get_collection_name()]
    cursor = collection.find().sort([('_id', 1)])

    entries = [
        Model(**entry) \
        for entry in await cursor.to_list(int(req._query_params.get("size", "50")))
    ]

    return paginate(entries)


@router.get("/models/objects/{object_id}")
async def retrieve_object(req: Request, object_id: str, app_name: str, model_name: str):
    Model: models.Model = get_model(app_name, model_name)
    if "get" not in Model.Meta.allowed_operations:
        raise exceptions.HTTPException(status.HTTP_403_FORBIDDEN, "Permission denied")

    collection: Collection = req.app.db[Model.get_collection_name()]
    try:
        db_obj = await collection.find_one({"_id": ObjectId(object_id)})
    except Exception as e:
        raise exceptions.HTTPException(500, f"error: {e}")
    
    if db_obj is None:
        raise exceptions.HTTPException(404, "Object not found")
    
    del db_obj["id"]
    db_obj["_id"] = str(db_obj["_id"])
    return db_obj


@router.post("/models/objects/", response_model=CreateObject)
async def create_objects(req: Request, payload: CreateObject):
    Model: models.Model = get_model(payload.app_name, payload.model_name)
    if "post" not in Model.Meta.allowed_operations:
        raise exceptions.HTTPException(status.HTTP_403_FORBIDDEN, "Permission denied")

    model_obj = Model(**payload.data)
    saved_obj = await model_obj.save(req.app.db)
    del saved_obj["id"]
    return { **payload.dict(), "data": saved_obj }


@router.patch("/models/objects/", response_model=UpdateObject)
async def update_object(req: Request, payload: UpdateObject):
    Model: models.Model = get_model(payload.app_name, payload.model_name)
    if "update" not in Model.Meta.allowed_operations:
        raise exceptions.HTTPException(status.HTTP_403_FORBIDDEN, "Permission denied")

    collection: Collection = req.app.db[Model.get_collection_name()]
    try:
        db_collection = await collection.find_one_and_update(
            {"_id": ObjectId(payload.object_id)},
            {"$set": payload.data},
            return_document=ReturnDocument.AFTER
        )
    except errors.DuplicateKeyError as e:
        raise exceptions.HTTPException(400, e.details["errmsg"])
    except Exception as e:
        raise exceptions.HTTPException(500, f"error: {e}")

    if db_collection is None:
        raise exceptions.HTTPException(404, "Object not found")

    del db_collection["id"]
    return {**payload.dict(), "data": db_collection}


@router.delete("/models/objects/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_object(req: Request, payload: DeleteObject):
    Model: models.Model = get_model(payload.app_name, payload.model_name)
    if "delete" not in Model.Meta.allowed_operations:
        raise exceptions.HTTPException(status.HTTP_403_FORBIDDEN, "Permission denied")

    collection: Collection = req.app.db[Model.get_collection_name()]
    try:
        db_collection = await collection.find_one_and_delete({
            "_id": ObjectId(payload.object_id)
        })
    except Exception as e:
        raise exceptions.HTTPException(500, f"error: {e}")

    if db_collection is None:
        raise exceptions.HTTPException(404, "Object not found")


add_pagination(router)
