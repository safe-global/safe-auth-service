#!/bin/bash

set -euo pipefail

export ENV_FILE=.env.test
docker compose -f docker-compose.yml build --force-rm redis
docker compose -f docker-compose.yml up --no-start redis
docker compose -f docker-compose.yml start redis

sleep 10

pytest -rxXs