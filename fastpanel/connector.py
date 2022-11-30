import importlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastpanel import settings, core


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

async def init_fastpanel(config_file: str):
    setattr(settings, "CONFIG_FILE_PATH", config_file)
    driver_module = importlib.import_module(settings.DATABASE["driver"])
    driver = driver_module.Driver()
    client, db = driver.connect()

    await driver.initialize_models(db)

    if not isinstance(client, type(None)):
        setattr(app, "client", client)
    if not isinstance(db, type(None)):
        setattr(app, "db", db)
    
    

async def deinit_fastpanel():
    driver_module = importlib.import_module(settings.DATABASE["driver"])
    driver = driver_module.Driver()

    client = getattr(app, "client", None)
    if not isinstance(client, type(None)):
        driver.disconnect(client)


app.include_router(core.routers.router, tags=["fastPanel"])
