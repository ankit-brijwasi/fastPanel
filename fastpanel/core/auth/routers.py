from fastapi import APIRouter, Depends, exceptions
from fastapi.security import OAuth2PasswordRequestForm
from pymongo import ReturnDocument

from .schemas import LoginRes
from .utils import verify_password, create_auth_tokens
from ..accounts import FastPanelUser
from ...utils import timezone


router = APIRouter()


@router.post("/login", response_model=LoginRes)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    error =  exceptions.HTTPException(400, "Incorrect username or password")
    collection = FastPanelUser.get_collection()
    document = await collection.find_one({"username": form_data.username})
    if not document: raise error

    user = FastPanelUser(**document)
    if not user.is_active: raise exceptions.HTTPException(403, "User is inactive")

    try:
        if not verify_password(form_data.password, user.password):
            raise error
    except Exception as e:
        print(e)
        raise exceptions.HTTPException(400, "Incorrect password! Please try again")

    document = await collection.find_one_and_update(
        {"_id": user.id},
        {"$set": {"last_login": timezone.now()}},
        return_document=ReturnDocument.AFTER
    )

    tokens = create_auth_tokens(user)
    return {**tokens, "user": FastPanelUser(**document)}
