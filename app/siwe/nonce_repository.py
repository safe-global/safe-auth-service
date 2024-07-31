from functools import cache

import siwe
from redis import Redis

from ..config import settings


@cache
def get_nonce_repository():
    redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return NonceRepository(redis_client=redis_client)


class NonceRepository:
    def __init__(self, redis_client: "Redis"):
        self.redis_client = redis_client

    def generate_nonce(self) -> str:
        nonce = siwe.generate_nonce()
        self.redis_client.set(nonce, nonce, ex=settings.NONCE_TTL_SECONDS)
        return nonce
