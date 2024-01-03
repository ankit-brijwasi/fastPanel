import asyncio
import pathlib
import click

from .core import Setup
from .utils import parse_config_file


async def push_data(collection, data): return await collection.insert_one(data)


@click.group()
@click.option(
    "--config_file",
    prompt="Path for the fastpanel config file",
    default="fastpanel.yaml",
    type=str,
)
@click.pass_context
def cli(ctx, config_file):
    path = pathlib.Path(config_file)
    if not path.is_file():
        raise FileNotFoundError(
            "Unable to find the config file at: %s" % (config_file)
        )
    ctx.obj = {"config_file": config_file}


@cli.command()
@click.pass_context
@click.option('--username', prompt="Enter your username", type=str)
@click.option('--email', type=str, default=None)
@click.option('--first_name', type=str, default=None)
@click.option('--last_name', type=str, default=None)
def createuser(ctx, username: str, email: str, first_name: str, last_name: str):
    password = click.prompt(
        "Enter your password",
        hide_input=True,
        confirmation_prompt=True,
        type=str
    )
    config = parse_config_file(ctx.obj["config_file"])
    config.pop("apps")
    Setup.load_settings(**config)

    from .core.accounts import FastPanelUser
    from .db.utils import get_db_client

    FastPanelUser._conn = get_db_client()
    user = FastPanelUser(
        username=username,
        password=password,
        email=email,
        first_name=first_name,
        last_name=last_name
    )
    collection = user.get_collection()
    asyncio.run(push_data(collection, user.model_dump(True)))


if __name__ == '__main__':
    cli()
