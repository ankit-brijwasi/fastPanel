from motor.core import Collection
from fastapi import APIRouter, Depends, Request, exceptions
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import bcrypt

from .schemas import FastPanelUser, LoginRes


router = APIRouter()
router.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/login", response_model=LoginRes)
async def login(req: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    collection: Collection = req.app.db["fastpanelusers"]
    user = await collection.find_one({"username": form_data.username})
    if not user:
        raise exceptions.HTTPException(400, "Incorrect username or password")
    
    user = FastPanelUser(**user)
    if not bcrypt.checkpw(form_data.password.encode("utf-8"), user.password.encode("utf-8")):
        raise exceptions.HTTPException(400, "Incorrect username or password")
    
    if not user.is_active:
        raise exceptions.HTTPException(403, "This user is inactive")

    # generate refresh and access token
    return {"access_token": "123", "refresh_token": "456", "user": user}

