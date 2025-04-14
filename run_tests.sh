#!/bin/bash

set -euo pipefail

export ENV_FILE=.env.test
docker compose -f docker-compose.yml build --force-rm redis db apisix mail
docker compose -f docker-compose.yml up --no-start redis db apisix mail
docker compose -f docker-compose.yml start redis db apisix mail

sleep 10
# Run migrations
alembic upgrade head
pytest -rxXs