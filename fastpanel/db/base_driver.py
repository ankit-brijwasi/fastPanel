from abc import ABC, abstractclassmethod
from typing import Tuple

import pymongo


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
                        "unique": True
                    }
                ]
            },
            "fastpanelactivities": {
                "$jsonSchema": {
                    "bsonType": "object",
                    "title": "FastPanelActivities object Validation",
                    "required": ["fastpaneluser_id", "message", "created_at"],
                    "properties": {
                        "fastpaneluser_id": {
                            "bsonType": "objectId",
                            "description": "'fastpaneluser_id' must be a objectId and is required"
                        },
                        "message": {
                            "bsonType": "object",
                            "description": "'message' must be an object and is required"
                        },
                        "created_at": {
                            "bsonType": ["date", "null"],
                            "description": "'created_at' must be a date"
                        }
                    }
                },
                "indexes": [
                    {"keys": "fastpaneluser_id"},
                    {"keys": "message"},
                ]
            }
        }

    @abstractclassmethod
    def construct_db_url(self) -> str:
        pass

    @abstractclassmethod
    def connect(self) -> Tuple:
        pass
    
    @abstractclassmethod
    def disconnect(self, client):
        pass
    
    @abstractclassmethod
    def initialize_models(self, db):
        pass