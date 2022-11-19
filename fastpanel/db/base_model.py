import pydantic


class Manager:
    ...


class Model(pydantic.BaseModel):
    def __generate_model_name(self):
        model_name = self.__class__.__name__.lower()
        return model_name + "s"

    def __init__(self, **data):
        super().__init__(**data)
        self._model_name = self.__generate_model_name()
        self.objects = Manager()