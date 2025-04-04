from datetime import UTC, datetime, timedelta

import siwe
from eth_typing import HexStr
from safe_eth.eth.utils import fast_to_checksum_address
from siwe.siwe import ISO8601Datetime, SiweMessage, VersionEnum

from ..config import settings
from ..datasources.cache.redis import get_redis
from ..exceptions import (
    InvalidMessageFormatError,
    InvalidNonceError,
    InvalidSignatureError,
)
from ..models.siwe_auth import SiweMessageInfo

CACHE_NONCE_PREFIX = "nonce:"


def generate_nonce() -> str:
    """
    Generates a new nonce to be used in the Sign-in with Ethereum process (EIP-4361).
    The nonce is cached for future validation. The cache lifetime is configured by NONCE_TTL_SECONDS key.

    Returns:
        Alphanumeric random character string of at least 8 characters.
    """
    nonce = siwe.generate_nonce()
    get_redis().set(CACHE_NONCE_PREFIX + nonce, nonce, ex=settings.NONCE_TTL_SECONDS)
    return nonce


def is_nonce_valid(nonce: str) -> bool:
    """
    Checks if the provided nonce is valid by verifying its existence in the cache.

    Args:
        nonce: The nonce string to validate.

    Returns:
        `True` if the nonce exists in the cache and is valid, `False` otherwise.
    """
    return bool(get_redis().exists(CACHE_NONCE_PREFIX + nonce))


def clear_nonce(nonce: str) -> bool:
    """
    Removes the provided nonce from the cache, invalidating it.

    Args:
        nonce: The nonce string to be removed from the cache.

    Returns:
        `True` if the nonce was successfully deleted, `False` if the nonce could not be deleted.
    """
    return bool(get_redis().delete(CACHE_NONCE_PREFIX + nonce))


def create_siwe_message(
    domain: str, address: str, chain_id: int, uri: str, statement=None
) -> str:
    """
    Creates a new Sign-in with Ethereum (EIP-4361) message.

    Args:
        domain: The domain that is requesting the signing. Its value MUST be an RFC 3986 authority.
        address: The Ethereum address performing the signing.
        chain_id: The Chain ID to which the session is bound.
        uri: An RFC 3986 URI referring to the resource that is the subject of the signing.
        statement: OPTIONAL. A human-readable assertion to show in the message that the user will sign.

    Returns:
        EIP-4361 formatted message, ready for EIP-191 signing.
    """
    nonce = generate_nonce()

    message = SiweMessage(
        domain=domain,
        address=fast_to_checksum_address(address),
        statement=statement or settings.DEFAULT_SIWE_MESSAGE_STATEMENT,
        uri=uri,
        version=VersionEnum.one,
        chain_id=chain_id,
        nonce=nonce,
        issued_at=ISO8601Datetime.from_datetime(datetime.now(UTC)),
        expiration_time=ISO8601Datetime.from_datetime(
            datetime.now(UTC) + timedelta(seconds=settings.NONCE_TTL_SECONDS)
        ),
    )

    return message.prepare_message()


def verify_siwe_message(message: str, signature: HexStr) -> None:
    """
    Verifies a Sign-In with Ethereum (SIWE) message and its associated signature.

    Args:
        message: The SIWE message as a string that needs to be verified.
        signature: The cryptographic signature associated with the SIWE message.

    Returns:
        None. If no exceptions are raised, the message and signature are considered valid
        and the nonce is cleared from the cache to prevent reuse.

    Raises:
        InvalidMessageFormatError: If the SIWE message format is invalid or unparseable.
        InvalidNonceError: If the nonce included in the SIWE message is invalid or expired.
        InvalidSignatureError: If the provided signature does not match the SIWE message.
    """
    try:
        siwe_message = SiweMessage.from_message(message)
    except ValueError:
        raise InvalidMessageFormatError("The SIWE message format is invalid.")

    if not is_nonce_valid(siwe_message.nonce):
        raise InvalidNonceError("The nonce provided in the SIWE message is invalid.")

    try:
        siwe_message.verify(signature=signature)
    except siwe.VerificationError:
        raise InvalidSignatureError("The SIWE signature is invalid.")

    clear_nonce(siwe_message.nonce)


def get_siwe_message_info(message: str) -> SiweMessageInfo:
    """
    Extracts essential information from a Sign-In with Ethereum (SIWE) message.

    Args:
        message: The SIWE message as a string that needs to be parsed.

    Returns:
        A `SiweMessageInfo` object.

    Raises:
        InvalidMessageFormatError: If the SIWE message format is invalid or unparseable.

    """
    try:
        siwe_message = SiweMessage.from_message(message)
        return SiweMessageInfo(
            chain_id=siwe_message.chain_id, signer_address=siwe_message.address
        )
    except ValueError:
        raise InvalidMessageFormatError("The SIWE message format is invalid.")
