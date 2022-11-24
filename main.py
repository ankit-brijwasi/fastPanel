from fastapi import FastAPI
import fastpanel.connector as connector


app = FastAPI()


@app.on_event("startup")
async def startup():
    await connector.init_fastpanel("./fastpanel.ini")


@app.on_event("shutdown")
async def shutdown():
    await connector.deinit_fastpanel()


app.mount("/fastpanel", connector.app)

