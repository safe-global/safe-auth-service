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
    ORIGINS: list[str] = []
    # Redis
    REDIS_URL: str = "redis://"
    # Database
    DATABASE_URL: str = "psql://postgres:"
    DATABASE_POOL_CLASS: str = "AsyncAdaptedQueuePool"
    DATABASE_POOL_SIZE: int = 10
    # Register
    PRE_REGISTRATION_TOKEN_TTL_SECONDS: int = 60 * 10  # 10 minutes

    # Email -----------------
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_SERVER: str = ""
    SMTP_PORT: int = 25
    SMTP_STARTTLS: bool = False
    SMTP_FROM_ADDRESS: str = "safe-auth-service-no-reply@safe.global"
    SMTP_TEST_API_URL: str = ""  # API url for testing smtp4dev

    # JWT -------------------
    # https://pyjwt.readthedocs.io/en/stable/usage.html#encoding-decoding-tokens-with-es256-ecdsa
    JWT_ALGORITHM: str = "ES256"
    JWT_AUDIENCE: list[str] = ["safe-auth-service"]
    JWT_AUTH_SERVICE_EXPIRE_DAYS: int = 7  # 1 week
    JWT_API_KEY_EXPIRE_DAYS: int = 1 * 365  # 1 year
    JWT_ISSUER: str = "safe-auth-service"
    JWT_PRIVATE_KEY: str = ""
    JWT_PUBLIC_KEY: str = ""

    # Google Auth
    GOOGLE_AUTHORIZATION_URL: str = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/google/callback"
    GOOGLE_TOKEN_URL: str = "https://accounts.google.com/o/oauth2/token"

    # Apisix ---------------
    APISIX_BASE_URL: str = ""
    APISIX_API_KEY: str = ""
    APISIX_CONNECTIONS_POOL_SIZE: int = 100

    # Apisix Consumer Groups (Payment Plans) ---------------
    APISIX_FREEMIUM_CONSUMER_GROUP_REQUESTS_PER_SECOND_MAX: int = 10
    APISIX_FREEMIUM_CONSUMER_GROUP_REQUESTS_PER_SECOND_TIME_WINDOW_SECONDS: int = 1
    APISIX_FREEMIUM_CONSUMER_GROUP_API_KEY_CREATION_LIMIT: int = 10

    # Datadog ---------------
    DATADOG_BASE_URL: str = "https://api.datadoghq.eu"
    DATADOG_API_KEY: str = ""
    DATADOG_APP_KEY: str = ""
    DATADOG_CONNECTIONS_POOL_SIZE: int = 100

    # Prometheus ---------------
    PROMETHEUS_BASE_URL: str = ""
    PROMETHEUS_CONNECTIONS_POOL_SIZE: int = 100

    # URLS
    FRONTEND_BASE_URL: str = ""

    # Event Service ---------------
    EVENTS_SERVICE_BASE_URL: str = ""
    EVENTS_SERVICE_API_KEY: str = ""
    EVENTS_SERVICE_CONNECTIONS_POOL_SIZE: int = 100
    EVENTS_SERVICE_WEBHOOKS_CREATION_LIMIT: int = 5


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

if not settings.TEST:
    # Prevent JSON error logs when running tests
    logging.config.dictConfig(LOGGING_CONFIG)
