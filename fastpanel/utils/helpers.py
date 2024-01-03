import yaml
from pydantic import validate_call, FilePath


@validate_call
def parse_config_file(config_file: FilePath):
    """
    Parse the fastpanel config file
    """
    with open(config_file, 'r') as config:
        config = yaml.safe_load(config)
        if 'database' in config and 'name' not in config["database"]:
            raise TypeError("Please pass the database name in the configuration")
    return config

