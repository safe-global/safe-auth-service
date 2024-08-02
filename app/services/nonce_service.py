import siwe

from ..cache import get_redis
from ..config import settings


def generate_nonce() -> str:
    """
    Generates a new nonce to be used in the Sign-in with Ethereum process (EIP-4361).
    The nonce is cached for future validation. The cache lifetime is configured by NONCE_TTL_SECONDS key.

    :return: Alphanumeric random character string of at least 8 characters.
    """
    nonce = siwe.generate_nonce()
    get_redis().set(nonce, nonce, ex=settings.NONCE_TTL_SECONDS)
    return nonce
