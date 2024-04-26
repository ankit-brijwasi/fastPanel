from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..conf import settings
from ..db.utils import Model, get_db_client


def load_cors_config(config):
    if "cors" in config:
        if not isinstance(config["cors"], dict):
            raise ValueError("cors must be a dict")

        req_keys = (
            "allow_origins",
            "allow_credentials",
            "allow_methods",
            "allow_headers"
        )
        missing_elements = [req_key for req_key in req_keys if req_key not in config["cors"]]
        if not len(missing_elements) == 0:
            raise ValueError("missing: %s" % (", ".join(missing_elements)))

    else:
        config["cors"] = {
            "allow_origins": ["*"],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"]
        }


class Setup:

    @staticmethod
    def load_settings(
        secret_key: str,
        apps: List[str] = [],
        models_lookup: str = None,
        db_connection = None,
        **extra
    ):
        if models_lookup: settings.MODELS_LOOKUP = models_lookup

        # load the apps and models
        for app_name in apps:
            app = settings.InstalledApp(app_name)
            settings.INSTALLED_APPS.append(app)
        
        # load cors
        load_cors_config(extra)

        # set extra args as attributes
        for key, value in extra.items():
            setattr(settings, key.upper(), value)

        settings.INSTALLED_APPS.extend([
            settings.InstalledApp("fastpanel.core.accounts", "models"),
        ])
        settings.SECRET_KEY = secret_key
        settings.SETTINGS_LOADED = True

        # set database connection reference to Model
        if not db_connection: db_connection = get_db_client()
        Model._conn = db_connection

        return settings

    @staticmethod
    async def load_models(connection):
        db = getattr(connection, settings.DATABASE["name"])
        models_available = await db.list_collection_names()
        missing_models = [
            req_model
            for app in settings.INSTALLED_APPS
            for req_model in app.models
            if req_model._meta.default.install_model and \
               not req_model._meta.default.is_nested and \
               not req_model.get_collection_name() in models_available
        ]

        for model in missing_models:
            print(f"installing {model.get_collection_name()} model...")
            collection_name, validation_schema = model.get_bson_schema()
            await db.create_collection(collection_name, validator=validation_schema)

            for index in model._meta.default.indexes:
                print("adding index:", index)
                await db[collection_name].create_index(**index)

    @staticmethod
    async def load_middlewares(app: FastAPI):
        app.add_middleware(CORSMiddleware, **settings.CORS)

