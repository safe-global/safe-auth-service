![Build Status](https://github.com/safe-global/safe-auth-service/workflows/Python%20CI/badge.svg?branch=main)
[![Coverage Status](https://coveralls.io/repos/github/safe-global/safe-auth-service/badge.svg?branch=main)](https://coveralls.io/github/safe-global/safe-auth-service?branch=main)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)
![Flask 3](https://img.shields.io/badge/Flask-3-blue.svg)

# Safe Auth Service
Grants JWT tokens based on ERC-4361 authentication.

## Configuration
```bash
cp .env.sample .env
```

## Execution

```bash
docker compose build
docker compose up
```

Then go to http://localhost:8888 to see the service documentation.

## Setup for development
Use a virtualenv if possible:

```bash
python -m venv venv
```

Then enter the virtualenv and install the dependencies:

```bash
source venv/bin/activate
pip install -r requirements/dev.txt
pre-commit install -f
cp .env.sample .env
```


## Contributors
[See contributors](https://github.com/safe-global/safe-auth-service/graphs/contributors)
