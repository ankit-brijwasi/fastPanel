import inspect

from motor.motor_asyncio import AsyncIOMotorClient

from .models import Model


def find_models(module, app_name):
    return (
        obj for _, obj in inspect.getmembers(module)
        if (
            inspect.isclass(obj) and
            issubclass(obj, Model) and
            obj.__module__.startswith(app_name)
        )
    )


def get_db_url():
    from ..conf import settings
    return "mongodb+srv://{}:{}@{}/?retryWrites=true&w=majority".format(
        settings.DATABASE['user'],
        settings.DATABASE['password'],
        settings.DATABASE['host']
    )


def get_db_client():
    from ..conf import settings
    if not settings.DATABASE:
        raise TypeError(
            "Please pass either the connection to db or "
            "the database info in the config file"
        )

    return AsyncIOMotorClient(get_db_url(), serverSelectionTimeoutMS=60000)


def get_model(app_name: str = "fastpanel.core.accounts", model_name: str = "FastPanelUser") -> Model:
    from ..conf import settings
    try:
        app: settings.InstalledApp = list(filter(lambda x: x.app_name == app_name, settings.INSTALLED_APPS))[0]
        for model in app.models:
            if model.__name__.lower().endswith(model_name.lower()):
                return model
    except IndexError: pass
    return None


def get_model_via_collection_name(collection_name: str):
    from ..conf import settings
    def search(installed_app: settings.InstalledApp):
        model = next(filter(lambda x: x.get_collection_name() == collection_name, installed_app.models), None)
        return model

    try:
        return next(map(search, settings.INSTALLED_APPS), None)
    except StopIteration: pass
    return None
