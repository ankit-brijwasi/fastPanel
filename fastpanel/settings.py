from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

ALLOWED_ORIGINS = ["http://localhost:8000"]

DATABASE = {
    "driver": "fastpanel.db.drivers.mongodb",
    "host": os.environ["DB_HOST"],
    "name": os.environ["DB_NAME"],
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"]
}

TIMEZONE = "UTC"

SECRET_KEY = "fatpanel_project_027e73e8e7adb8711c3b51e88efef31a7c08cb9f88d055a06f547a5034a409a7"
JWT_CONF = {
    "ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRY": timedelta(days=7)
}

