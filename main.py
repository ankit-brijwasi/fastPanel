from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from fastpanel.db.drivers import Driver
from fastpanel import connector

from devduels.routers import router


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


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
app.include_router(router, tags=["DevDuels"])

app.mount("/", StaticFiles(directory="preact-app/", html=True), name="preact-app")