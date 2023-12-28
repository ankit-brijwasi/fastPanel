class SettingsNotLoaded(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(
            "Settings are not loaded yet! "
            "Please call the `init()` before mounting the application",
            *args
        )
