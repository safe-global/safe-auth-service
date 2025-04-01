[![Python CI](https://github.com/safe-global/safe-auth-service/actions/workflows/ci.yml/badge.svg)](https://github.com/safe-global/safe-auth-service/actions/workflows/ci.yml)
[![Coverage Status](https://coveralls.io/repos/github/safe-global/safe-auth-service/badge.svg?branch=main)](https://coveralls.io/github/safe-global/safe-auth-service?branch=main)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)
[![Docker Image Version (latest semver)](https://img.shields.io/docker/v/safeglobal/safe-auth-service?label=Docker&sort=semver)](https://hub.docker.com/r/safeglobal/safe-auth-service)


# Safe Auth Service
Grants JWT tokens to be used across the Safe Core{API} infrastructure. It supports ERC-4361 authentication.

## Configuration
```bash
cp .env.sample .env
```

## Execution

```bash
docker compose build
docker compose up
```

Then go to http://localhost:8000 to see the service documentation.

## Setup for development
Use a virtualenv if possible:

```bash
python -m venv venv
```

Then enter the virtualenv and install the dependencies:

```bash
source venv/bin/activate
pip install -r requirements.txt
pre-commit install -f
cp .env.sample .env
```

### Handle migrations
This projects is using [Alembic](https://alembic.sqlalchemy.org/en/latest/) to manage database migrations.
To create a new migration based on changes made to the model code, run the following command:

```bash
alembic revision --autogenerate -m "MIGRATION TITLE"
```

### Querying the database via Python Shell in Docker
To open an interactive Python shell within a Docker container and query the database, use the following command:
```
 docker exec -it safe-decoder-service-web-1 python -m IPython -i ./scripts/db_profile.py
```
Example usage:
```python
users = await Users.get_all()
print(users[0].email)
```
Call `await restore_session()` to reopen a new session.

## Contributors
[See contributors](https://github.com/safe-global/safe-auth-service/graphs/contributors)
