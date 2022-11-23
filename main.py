import importlib

from fastapi import FastAPI
import uvicorn

from fastpanel import settings, core


app = FastAPI()


@app.on_event("startup")
async def startup():
    driver_module = importlib.import_module(settings.DATABASE["driver"])
    driver = driver_module.Driver()
    client, db = driver.connect()

    await driver.initialize_models(db)

    if not isinstance(client, type(None)):
        setattr(app, "client", client)
    if not isinstance(db, type(None)):
        setattr(app, "db", db)


@app.on_event("shutdown")
async def shutdown():
    driver_module = importlib.import_module(settings.DATABASE["driver"])
    driver = driver_module.Driver()

    client = getattr(app, "client", None)
    if not isinstance(client, type(None)):
        driver.disconnect(client)


app.include_router(core.routers.router, prefix="/fastpanel", tags=["fastPanel"])


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, host="127.0.0.1", port=8000)
