import configparser
import importlib

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


def get_model(import_path: str):
    return importlib.import_module(import_path)