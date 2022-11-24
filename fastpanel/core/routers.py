from datetime import timedelta

from fastapi import APIRouter, Depends, Request, Response, exceptions
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from motor.core import Collection
from pymongo import ReturnDocument

import bcrypt

from .schemas import FastPanelUser, LoginRes
from ..utils.auth import create_access_token
from ..utils import timezone
from fastpanel import settings
from fastpanel.utils.helpers import collect_models


router = APIRouter()
router.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


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
    if not bcrypt.checkpw(form_data.password.encode("utf-8"), user.password.encode("utf-8")):
        raise error

    if not user.is_active:
        raise exceptions.HTTPException(403, "This user is inactive")

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


@router.post("/fetch-models")
async def fetch_models():
    assert hasattr(settings, "CONFIG_FILE_PATH"), "config file is not present"
    return collect_models(getattr(settings, "CONFIG_FILE_PATH"))