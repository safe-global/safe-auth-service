[![Python CI](https://github.com/safe-global/safe-auth-service/actions/workflows/ci.yml/badge.svg)](https://github.com/safe-global/safe-auth-service/actions/workflows/ci.yml)
[![Coverage Status](https://coveralls.io/repos/github/safe-global/safe-auth-service/badge.svg?branch=main)](https://coveralls.io/github/safe-global/safe-auth-service?branch=main)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)
[![Docker Image Version (latest semver)](https://img.shields.io/docker/v/safeglobal/safe-auth-service?label=Docker&sort=semver)](https://hub.docker.com/r/safeglobal/safe-auth-service)


# Safe Auth Service
Grants JWT tokens to be used across the Safe Core{API} infrastructure.

## Configuration
```bash
cp .env.docker .env
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
cp .env.docker .env
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
users = await User.get_all()
print(users[0].email)
```
Call `await restore_session()` to reopen a new session.

## Test full workflow locally

```bash
cp .env.docker .env
docker compose pull
docker compose up -d
```

Once everything is ready, go to http://localhost:9000/ to configure **Apisix** using the Dashboard:
1. Credentials are `admin:dashboard`.
2. Go to **plugin** and enable `jwt-auth` and `prometheus`.
3. Configure an **upstream** (remember to set `Hostname` to `Use the domain or IP from Node List`), and then configure
a **route** pointing to the **upstream**.
4. Test the route `curl http://127.0.0.1:9080/`

After **Apisix** is configured, time to create a user to interact with it. Go to http://localhost:8000/ for
the **Safe Auth Service API**:
1. Call `preregister` endpoint. Any email will do.
2. Go to the email local server on http://localhost:2526/ , and check the token.
3. Use the `register` endpoint with the token.
4. With the `password` and `email`, `login` (swagger has a very convenient `authorize` button on top right).
5. Create an api key using POST `/api-keys` endpoint. Set a good description that will appear lately on the Apisix consumers panel.
Note the `key` attribute, it's the `JWT` token to use it with Apisix.
6. Call apisix route using `curl -H "Authorization: $JWT_KEY" 'http://127.0.0.1:9080/'`

You can go now to the **Apisix** dashboard and check the consumers, and also to **Prometheus**
on http://localhost:9090/ and query the monitoring data, for example using the key `apisix_http_status`.


## Contributors
[See contributors](https://github.com/safe-global/safe-auth-service/graphs/contributors)
