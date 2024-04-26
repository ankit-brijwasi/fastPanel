from setuptools import find_packages, setup

setup(
    name="fastpanel",
    version="1.0.0",
    description="A library that makes the life of fARM stack developers easy",
    packages=find_packages(),
    package_data={"fastpanel": ["*.py", "preact-app/fast-panel/*"]},
    long_description="FastPanel is a modern version of the Django admin panel for FastAPI and MongoDB developers, with a Frontend powered using pReact",
    author="Ankit Brijwasi, Navdeep Mishra",
    author_email="abrijwasi1@gmail.com, navdeepmishra8270@gmail.com",
    maintainer="Ankit Brijwasi, Navdeep Mishra",
    maintainer_email="abrijwasi1@gmail.com, navdeepmishra8270@gmail.com",
    url="https://github.com/ankit-brijwasi/fastpanel",
    long_description_content_type="text/markdown",
    python_requires=">=3.7",
    install_requires=[
        "fastapi==0.104.0",
        "pymongo>=4.5.0",
        "uvicorn>=0.23.2",
        "PyYAML>=6.0.1",
        "motor>=3.3.1",
        "email-validator>=2.1.0",
        "dnspython>=2.4.2",
        "pydantic==2.4.2",
        "pydantic-core==2.10.1",
        "python-jose>=3.3.0",
        "python-multipart>=0.0.6",
        "pytz>=2023.3.post1",
        "passlib>=1.7.4",
        "bcrypt==4.0.1",
        "jsonschema>=4.20.0",
        "click>=8.1.7"
    ],
    entry_points={
        "console_scripts": [
            "fastpanel=fastpanel.cli:cli"
        ]
    }
)
