from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import FilePath

from . import core
from .utils import parse_config_file
from .db.models import Model


FRONTEND_DIR = Path(__file__).parent / "preact-app" / "fast-panel"
app = FastAPI()


# middleware to check whether settings are loaded or not
@app.middleware("http")
async def settings_loaded_middleware(request, call_next):
    from .conf import settings
    from .exceptions import SettingsNotLoaded

    if not settings.SETTINGS_LOADED: raise SettingsNotLoaded()
    return await call_next(request)


async def init(
        config_file: FilePath, root_app: FastAPI,
        mount_path: str = "/", conn = None
    ):
    # load settings
    config = parse_config_file(config_file)
    core.Setup.load_settings(db_connection=conn, **config)

    # load middlewares
    await core.Setup.load_middlewares(app)
    await core.Setup.load_models(Model._conn)

    app.include_router(core.auth_router, prefix="/auth", tags=["Auth"])
    app.include_router(core.accounts_router, prefix="/accounts", tags=["Account"])
    app.include_router(core.core_router, prefix="/core", tags=["Core"])
    app.mount(mount_path, StaticFiles(directory=str(FRONTEND_DIR), html=True), name="preact-app")

    # mount the root application
    root_app.mount("/fastpanel", app, name="FastPanel")


async def deinit():
    if hasattr(Model, "_conn"):
        Model._conn.close()

