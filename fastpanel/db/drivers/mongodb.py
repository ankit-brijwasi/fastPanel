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
        for inbuilt_model in self.inbuilt_models:
            if inbuilt_model not in models_available:
                logger.warning(f"{inbuilt_model} was not found! Creating it...")
                await db.create_collection(inbuilt_model)
