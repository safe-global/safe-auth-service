from functools import cache

import siwe
from redis import Redis

from ..config import settings


@cache
def get_nonce_repository() -> "NonceRepository":
    redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return NonceRepository(redis_client=redis_client)


class NonceRepository:
    def __init__(self, redis_client: "Redis"):
        self.redis_client = redis_client

    def generate_nonce(self) -> str:
        """
        Generates a new nonce to be used in the Sign-in with Ethereum process (EIP-4361).
        The nonce is cached for future validation. The cache lifetime is configured by NONCE_TTL_SECONDS key.

        :return: Alphanumeric random character string of at least 8 characters.
        """
        nonce = siwe.generate_nonce()
        self.redis_client.set(nonce, nonce, ex=settings.NONCE_TTL_SECONDS)
        return nonce
