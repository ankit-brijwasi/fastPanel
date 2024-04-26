from typing import List
import importlib
import logging


logger = logging.getLogger()

SETTINGS_LOADED = False

SECRET_KEY: str = ""

MODELS_LOOKUP: str = "models"

DEBUG = True

DATABASE = {}

TIMEZONE = "UTC"

class InstalledApp:
    def _discover_models(self):
        from ..db.utils import find_models
        try:
            module = importlib.import_module(f"{self.app_name}.{self.models_lookup}")
            return [model for model in find_models(module, self.app_name)]
        except ImportError:
            if not self.app_name.startswith("fastpanel"):
                logger.warning("No models present in app: %s" % (self.app_name))
            return []

    def __init__(self, app_name, models_lookup = MODELS_LOOKUP) -> None:
        self.app_name: str = app_name
        self.models_lookup = models_lookup
        self.models = self._discover_models()
    
    def __repr__(self) -> str:
        return f"<InstalledApp app_name='{self.app_name}'>"

INSTALLED_APPS: List[InstalledApp] = []

ACCESS_TOKEN_EXPIRATION: int = 3600

REFRESH_TOKEN_EXPIRATION: int = 86400

UI_MOUNT_URL: str = "/"