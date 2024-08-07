"""
Base settings file for FastApi application.
"""

import json
import logging.config
import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.environ.get("ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        extra="allow",
        case_sensitive=True,
    )
    REDIS_URL: str = "redis://"
    NONCE_TTL_SECONDS: int = 60 * 10
    DEFAULT_SIWE_MESSAGE_STATEMENT: str = (
        "Welcome to Safe! I accept the Terms of Use: https://safe.global/terms."
    )
    LOG_LEVEL: str = "INFO"


settings = Settings()


LOG_FORMAT = {
    "level": "%(levelname)s",
    "timestamp": "%(asctime)s",
    "message": "%(message)s",
    "context": "",
    "messageContext": "",
}

LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {"default": {"format": json.dumps(LOG_FORMAT)}},
    "handlers": {
        "console": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "level": settings.LOG_LEVEL,
        }
    },
    "root": {"handlers": ["console"], "level": settings.LOG_LEVEL},
    "loggers": {
        "gunicorn": {"propagate": True},
        "gunicorn.access": {"propagate": True},
        "gunicorn.error": {"propagate": True},
        "uvicorn": {"propagate": True},
        "uvicorn.access": {"propagate": True},
        "uvicorn.error": {"propagate": True},
    },
}

logging.config.dictConfig(LOG_CONFIG)
