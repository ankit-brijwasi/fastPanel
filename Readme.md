# FastPanel: The Modern Admin Panel for FastAPI and MongoDB Developers

Meet FastPanel – the new-age dashboard crafted for developers using FastAPI and MongoDB, with a user-friendly interface powered by pReact.

FastPanel steps up as the modern twist on the classic Django admin panel. It's tailored for folks diving into FastAPI and MongoDB, offering a smooth experience for managing your projects.

Think of it as your go-to tool for streamlining your work, letting you focus on what really counts – creating awesome apps.

So, get ready to explore the future of admin panels with FastPanel.

## Build and install the FastPanel library

- Build the library using-

```bash
$ python setup.py sdist
```

- Install the library

```bash
$ pip install dist/fastpanel-1.x.x.tar.gz
```

> FYI: pip version will be released soon!😉😁

## Configure FastPanel into your application

1. Create the `fastpanel.yaml` configuration file, here's the general format for that-

```yaml
secret_key: <MY SECRET KEY> # enter the secret key for your app, this key will be used for all the tokens
access_token_expiration: 36000
refresh_token_expiration: 860000
ui_mount_url: / # uri where the ui will be visible
database:
  host: <MONGODB DB Host>
  user: <MONGODB DB USER>
  password: <MONGODB DB PASSWORD>
  name: <MONGODB DB NAME>
apps: # add the apps which you want to register on the fastpanel UI, for now we'll keep it empty
cors:
  allow_origins: []
  allow_credentials: False
  allow_methods: ["GET"]
  allow_headers: []
```

2. Once done, open your entrypoint file (ex. `main.py`) and paste the following code-

```python
# main.py

# import packages
from contextlib import asynccontextmanager
from fastpanel import connector


# hook fastpanel into your application as a lifespan event
@asynccontextmanager
async def lifespan(app: FastAPI):
    conf_file = Path("/path/to/fastpanel/conf/file")
    await connector.init(conf_file, app)
    yield
    await connector.deinit()


app = FastAPI(lifespan=lifespan)

# rest of the code for your server
```

3. Now when you'll start your server, it will load fastpanel into your application without affecting your codebase

```bash
(env) ☁  fastPanel [master] ⚡ uvicorn main:app --host 127.0.0.1 --port 8000 --reload
INFO:     Will watch for changes in these directories: ['/home/ankit/projects/posts']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [4869] using StatReload
INFO:     Started server process [4871]
INFO:     Waiting for application startup.
INFO:     Mounting Fastpanel
INFO:     installing fastpanelusers model...
INFO:     adding index: {'keys': 'username', 'unique': True}
INFO:     adding index: {'keys': 'email', 'unique': True, 'partialFilterExpression': {'email': {'$type': 'string'}}}
INFO:     Mounted Fastpanel successfully! visit the /fastpanel/ route to view it!
INFO:     Application startup complete.
```

With this fastpanel, will be mounted as a sub app in your main application the route to access it will be, `{your base url}/fastpanel/` for example in this instance the url to access it would be, [127.0.0.1:8000/fastpanel/](http://127.0.0.1:8000/fastpanel/).

> Note: You can configure where to load the fastpanel UI by using, the `ui_mount_url` setting on the config file

## Create a new user to access fastpanel

FastPanel UI is login protected so in order to view it, you'll need to create a new user for accessing it, to do that use the following command

```bash
$ fastpanel createuser
Path for the fastpanel config file [fastpanel.yaml]: # leave it empty if the config file's name is fastpanel.yaml and it is present at the root dir only
Enter your username: <username>
Enter your password:
Repeat for confirmation:
```

## Install a new app and models in fastpanel

By following the above steps, fastpanel will loaded into your application, now to register new applications and models into it you'll need to do some more minor changes let's look into them.

Let's suppose you have blog project and you want to create a new app/python module in it called, `posts` to which will have a mongodb collection called `Post` where all the posts you create will be stored.

This is the directory structure-

```
|-posts
    |-__init__.py
    |-models.py
    |-controller.py
```

Let's suppose, that you are going to store your mongodb collection as pydantic schema in the `models.py` file, than all you need to do is instead of using the `BaseModel` class from pydantic, replace it with fastpanel's `Model` class, with that you can easily define the schema for your mongodb collection.

Here's how your model will look like-

```python

# models.py
from fastpanel.db.fields import Field
from fastpanel.db import models

class Post(models.Model):
    title: str = Field(json_schema_extra={"bsonType": "string"})
    body: str = Field(json_schema_extra={"bsonType": "string"})
    likes_count:int = Field(json_schema_extra={"bsonType":"int"})

```

Right now it won't be registered into the fastPanel UI, to do that you'll need to update your fastpanel config file's app section-

```yaml

---
# rest of the yaml configuration

apps:
  - posts
```

Once, you do this and restart the server, the models(collection) inside the `posts` app should be auto picked by fastpanel and they should be also created at your mongodb database

```bash
(env) ☁  fastPanel [master] ⚡ uvicorn main:app --host 127.0.0.1 --port 8000 --reload
INFO:     Will watch for changes in these directories: ['/home/ankit/projects/posts']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [8012] using StatReload
INFO:     Started server process [8014]
INFO:     Waiting for application startup.
INFO:     Mounting Fastpanel
INFO:     installing posts model...
INFO:     Mounted Fastpanel successfully! visit the /fastpanel/ route to view it!
INFO:     Application startup complete.
```

Now, refresh the fastpanel UI, youe app will start appearing there and you can easily view all the models inside your app!

> The models which you created, using Fastpanel are pydantic models at core, meaning that you can very easily integrate them with your fastapi application, and it will work there like a charm!

> FastPanel models are like, mongodb collection mapper with your fastapi application, meaning you can use them as a translation layer for your mongodb collections! All the standard operations which are available on `pydantic` BaseModel are available in the FastPanel models as well, so you can use that as it is!

> FastPanel models also supports Relation type fields, although right now only `EmbededField` is supported, but we are continously working to introduce newer fields like, `ReferenceField` into the system as well!

More documentation regarding fastpanel `models` will be added soon!
