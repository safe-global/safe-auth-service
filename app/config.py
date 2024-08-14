"""
Base settings file for FastApi application.
"""

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

    # https://pyjwt.readthedocs.io/en/stable/usage.html#encoding-decoding-tokens-with-rs256-rsa
    JWT_PRIVATE_KEY: str = ""  # RSA private key -----BEGIN ...
    JWT_ISSUER: str = "safe-auth-service"
    JWT_EXPIRATION_SECONDS: int = 24 * 60 * 60
    JWT_COOKIE_NAME: str = "safe_access_token"


settings = Settings()
