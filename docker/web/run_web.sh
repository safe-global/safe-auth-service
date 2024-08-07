#!/bin/bash

set -euo pipefail

echo "==> $(date +%H:%M:%S) ==> Collecting statics... "
DOCKER_SHARED_DIR=/nginx
rm -rf $DOCKER_SHARED_DIR/*
cp -r static/ $DOCKER_SHARED_DIR/

echo "==> $(date +%H:%M:%S) ==> Running Gunicorn with Uvicorn... "
# https://fastapi.tiangolo.com/deployment/server-workers/#server-workers-gunicorn-with-uvicorn
exec gunicorn app.main:app -k uvicorn.workers.UvicornWorker -b unix:$DOCKER_SHARED_DIR/uvicorn.socket -b 0.0.0.0:8888
