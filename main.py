import logging

from fastapi import FastAPI

from fastpanel.db.drivers import Driver
from fastpanel import connector

from devduels.routers import router


app = FastAPI()
logger = logging.getLogger()
process = None


@app.on_event("startup")
async def startup():
    await connector.init_fastpanel("./fastpanel.ini")
    client, db = Driver().connect()
    app.client = client
    app.db = db


@app.on_event("shutdown")
async def shutdown():
    await connector.deinit_fastpanel()


# mounted fastpanel
app.mount("/fastpanel", connector.app)


# internal routes
app.include_router(router, tags=["DevDuels"])