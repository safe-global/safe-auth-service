"""
Base settings file for FastApi application.
"""

import logging.config
import os

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.loggers.safe_logger import SafeJsonFormatter


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.environ.get("ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        extra="allow",
        case_sensitive=True,
    )
    TEST: bool = False
    LOG_LEVEL: str = "INFO"
    REDIS_URL: str = "redis://"
    NONCE_TTL_SECONDS: int = 60 * 10
    PRE_REGISTRATION_TOKEN_TTL_SECONDS: int = 60 * 10  # 10 minutes

    # https://pyjwt.readthedocs.io/en/stable/usage.html#encoding-decoding-tokens-with-rs256-rsa
    JWT_PRIVATE_KEY: str = ""  # RSA private key -----BEGIN ...
    JWT_ISSUER: str = "safe-auth-service"
    JWT_EXPIRATION_SECONDS: int = 24 * 60 * 60
    JWT_COOKIE_NAME: str = "safe_access_token"
    JWT_PUBLIC_KEY: str = ""  # RSA public key -----BEGIN ... To share with Apisix
    DATABASE_URL: str = "psql://postgres:"
    DATABASE_POOL_CLASS: str = "AsyncAdaptedQueuePool"
    DATABASE_POOL_SIZE: int = 10

    APISIX_CONNECTIONS_POOL_SIZE: int = 100


settings = Settings()

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"()": SafeJsonFormatter}},  # Custom formatter class
    "handlers": {
        "console": {
            "level": settings.LOG_LEVEL,
            "class": "logging.StreamHandler",
            "formatter": "json",
        }
    },
    "loggers": {
        "": {
            "level": settings.LOG_LEVEL,
            "handlers": ["console"],
            "propagate": False,
        }
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
