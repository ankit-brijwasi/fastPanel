import logging
import motor.motor_asyncio
from fastpanel import settings, db

logger = logging.getLogger()

class Driver(db.BaseDriver):
    """
    Driver for connecting to mongodb
    """

    def construct_db_url(self):
        return "mongodb+srv://{}:{}@{}/?retryWrites=true&w=majority".format(
            settings.DATABASE['user'],
            settings.DATABASE['password'],
            settings.DATABASE['host']
        )

    def connect(self):
        url = self.construct_db_url()
        client = motor.motor_asyncio.AsyncIOMotorClient(url, serverSelectionTimeoutMS=60000)
        database = getattr(client, settings.DATABASE["name"])
        return client, database

    def disconnect(self, client):
        client.close()

    async def initialize_models(self, db):  
        models_available = await db.list_collection_names()
        for key, value in self.inbuilt_models.items():
            if key not in models_available:
                kwargs = {}
                logger.warning(f"{key} was not found! Creating it...")

                if "$jsonSchema" in value.keys():
                    kwargs["validator"] = {"$jsonSchema": value["$jsonSchema"]}

                await db.create_collection(key, **kwargs)

                if "indexes" in value.keys():
                    for index in value["indexes"]:
                        await db[key].create_index(**index)

