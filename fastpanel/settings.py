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