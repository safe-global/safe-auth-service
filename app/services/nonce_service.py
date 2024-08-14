import siwe

from ..cache import get_redis
from ..config import settings

CACHE_NONCE_PREFIX = "nonce:"


def generate_nonce() -> str:
    """
    Generates a new nonce to be used in the Sign-in with Ethereum process (EIP-4361).
    The nonce is cached for future validation. The cache lifetime is configured by NONCE_TTL_SECONDS key.

    :return: Alphanumeric random character string of at least 8 characters.
    """
    nonce = siwe.generate_nonce()
    get_redis().set(CACHE_NONCE_PREFIX + nonce, nonce, ex=settings.NONCE_TTL_SECONDS)
    return nonce


def is_nonce_valid(nonce: str) -> bool:
    """
    Checks if the provided nonce is valid by verifying its existence in the cache.

    :param nonce: The nonce string to validate.
    :return: `True` if the nonce exists in the cache and is valid, `False` otherwise.
    """
    return bool(get_redis().exists(CACHE_NONCE_PREFIX + nonce))


def clear_nonce(nonce: str) -> bool:
    """
    Removes the provided nonce from the cache, invalidating it.

    :param nonce: The nonce string to be removed from the cache.
    :return: `True` if the nonce was successfully deleted, `False` if the nonce could not be deleted.
    """
    return bool(get_redis().delete(CACHE_NONCE_PREFIX + nonce))
