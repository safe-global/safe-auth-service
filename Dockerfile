FROM python:3.12-slim

EXPOSE 8888/tcp
ARG APP_HOME=/app
WORKDIR ${APP_HOME}

COPY requirements/prod.txt ./requirements.txt
RUN set -ex \
	&& buildDeps=" \
		build-essential \
        git \
		libssl-dev \
		" \
    && apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends $buildDeps \
    && pip install -U --no-cache-dir wheel setuptools pip \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove $buildDeps \
    && rm -rf /var/lib/apt/lists/* \
    && find /usr/local \
        \( -type d -a -name test -o -name tests \) \
        -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
        -exec rm -rf '{}' +

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8888", "--proxy-headers"]
