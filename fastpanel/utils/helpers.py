from functools import lru_cache
import configparser
import importlib

from fastapi import exceptions

@lru_cache
def collect_models(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)

    models = []
    for section in config.sections():
        app = {}
        app['name'] = section
        app['base_path'] = config[section]["path"]
        app['models'] = []

        for model in config[section]["registered_models"].split(","):
            app['models'].append(
                {
                    "name": model.split(".")[-1],
                    "import_path": f"{app['base_path']}.{model}"
                }
            )
        
        models.append(app)
    return models


get_app_models = lambda app_name, models: list(filter(lambda model: model["name"] == app_name, models))


def get_model(app_name, model_name):
    from fastpanel import settings
    try:
        models = get_app_models(app_name, collect_models(settings.CONFIG_FILE_PATH))[0]["models"]
        needed_model = list(filter(lambda x: x["name"].lower() == model_name.lower(), models))[0]
    except (KeyError, IndexError):
        raise exceptions.HTTPException(404, "model not found")
    
    import_path = needed_model["import_path"].split(".")
    module_path = ".".join(import_path[:-1])
    return getattr(importlib.import_module(module_path), import_path[-1])
