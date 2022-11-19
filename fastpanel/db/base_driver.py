from abc import ABC, abstractclassmethod
from typing import Tuple


class BaseDriver(ABC):
    """
    BaseDriver class for creating drivers. Always extend this
    class for creating new drivers
    """

    def __init__(self) -> None:
        super().__init__()
        self.inbuilt_models = ["fastpanelusers"]

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