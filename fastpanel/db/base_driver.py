from abc import ABC, abstractclassmethod
from typing import Tuple

from fastpanel import settings


class BaseDriver(ABC):
    """
    BaseDriver class for creating drivers. Always extend this
    class for creating new drivers
    """

    def __init__(self) -> None:
        super().__init__()
        self.inbuilt_models = {
            "fastpanelusers": {
                "$jsonSchema": {
                    "bsonType": "object",
                    "title": "FastPanelUser object Validation",
                    "required": ["username", "password", "email", "first_name", "last_name", "date_joined", "last_login", "is_active"],
                    "properties": {
                        "username": {
                            "bsonType": "string",
                            "description": "'username' must be a string and is required"
                        },
                        "password": {
                            "bsonType": "string",
                            "description": "'password' must be an string and is required"
                        },
                        "email": {
                            "bsonType": ["string", "null"],
                            "description": "'email' must be a string"
                        },
                        "first_name": {
                            "bsonType": ["string", "null"],
                            "description": "'first_name' must be a string"
                        },
                        "last_name": {
                            "bsonType": ["string", "null"],
                            "description": "'username' must be a string"
                        },
                        "date_joined": {
                            "bsonType": "date",
                            "description": "'date_joined' must be a date"
                        },
                        "last_login": {
                            "bsonType": ["date", "null"],
                            "description": "'last_login' must be a date if it is passed"
                        },
                        "is_active": {
                            "bsonType": "bool",
                            "description": "'bool' must be a boolean and is required"
                        }
                    }
                },
                "indexes": [
                    {            
                        "keys": "username",
                        "unique": True
                    },
                    {
                        "keys": "email",
                        "unique": True,
                        "partialFilterExpression": {"email": {"$type": "string"}}
                    }
                ]
            }
        }

    @classmethod
    def construct_db_url(self):
        return "mongodb+srv://{}:{}@{}/?retryWrites=true&w=majority".format(
            settings.DATABASE['user'],
            settings.DATABASE['password'],
            settings.DATABASE['host']
        )

    @abstractclassmethod
    def connect(self) -> Tuple:
        pass
    
    @abstractclassmethod
    def disconnect(self, client):
        pass
    
    @abstractclassmethod
    def initialize_models(self, db):
        pass