import yaml
import shutil
from pathlib import Path

from pydantic import validate_call, FilePath, DirectoryPath


@validate_call
def copy_files(source_dir: DirectoryPath, destination_dir: DirectoryPath, skip_files=None):
    source_path = Path(source_dir)
    destination_path = Path(destination_dir)
    destination_path.mkdir(parents=True, exist_ok=True)
    all_paths = source_path.glob('**/*')

    for path in all_paths:
        relative_path = path.relative_to(source_path)
        destination_item = destination_path / relative_path

        if path.is_file(): 
            if not skip_files and path.name in skip_files:
                destination_item.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, destination_item)
        else:
            destination_item.mkdir(parents=True, exist_ok=True)


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


@validate_call
def setup_frontend(frontend_dir: DirectoryPath):
    staticfiles_dir = frontend_dir.parent / "static"

    # check if staticfiles_dir exists
    if not staticfiles_dir.exists():
        from ..conf import settings

        # create the staticfiles_dir
        staticfiles_dir.mkdir(parents=True)

        # create the assets_dir
        assets_dir = staticfiles_dir / "assets"
        assets_dir.mkdir(parents=True)

        with open(frontend_dir / "assets" / "index.js", "r") as index_js:
            compiled_frontend_code = index_js.read()

        compiled_frontend_code = compiled_frontend_code.replace(
            "<FP_BASE_APP_URL>",
            "/fastpanel"
        )
        compiled_frontend_code = compiled_frontend_code.replace(
            "<FP_BASE_API_URL>",
            "http://localhost:8000/fastpanel"
        )

        with open(assets_dir / "index.js", "w") as f:
            f.write(compiled_frontend_code)
        
        copy_files(frontend_dir, staticfiles_dir, "index.js")

    return staticfiles_dir