from datetime import UTC, datetime, timedelta

import siwe
from siwe.siwe import ISO8601Datetime, SiweMessage, VersionEnum

from gnosis.eth.utils import fast_to_checksum_address

from ..config import settings
from ..exceptions import (
    InvalidMessageFormatError,
    InvalidNonceError,
    InvalidSignatureError,
)
from ..models import SiweMessageInfo
from .nonce_service import clear_nonce, generate_nonce, is_nonce_valid


def create_siwe_message(
    domain: str, address: str, chain_id: int, uri: str, statement=None
) -> str:
    """
    Creates a new Sign-in with Ethereum (EIP-4361) message.

    :param domain: The domain that is requesting the signing. Its value MUST be an RFC 3986 authority.
    :param address: The Ethereum address performing the signing.
    :param chain_id: The Chain ID to which the session is bound.
    :param uri: An RFC 3986 URI referring to the resource that is the subject of the signing.
    :param statement: OPTIONAL. A human-readable assertion to show in the message that the user will sign.
    :return: EIP-4361 formatted message, ready for EIP-191 signing.
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


def verify_siwe_message(message: str, signature: str) -> None:
    """
    Verifies a Sign-In with Ethereum (SIWE) message and its associated signature.

    :param message: The SIWE message as a string that needs to be verified.
    :param signature: The cryptographic signature associated with the SIWE message.
    :raises InvalidMessageFormatError: If the SIWE message format is invalid or unparseable.
    :raises InvalidNonceError: If the nonce included in the SIWE message is invalid or expired.
    :raises InvalidSignatureError: If the provided signature does not match the SIWE message.
    :return: None. If no exceptions are raised, the message and signature are considered valid
        and the nonce is cleared from the cache to prevent reuse.
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

    :param message: The SIWE message as a string that needs to be parsed.
    :raises InvalidMessageFormatError: If the SIWE message format is invalid or unparseable.
    :return: A `SiweMessageInfo` object or `None` if the message format is invalid.
    """
    try:
        siwe_message = SiweMessage.from_message(message)
        return SiweMessageInfo(
            chain_id=siwe_message.chain_id, signer_address=siwe_message.address
        )
    except ValueError:
        raise InvalidMessageFormatError("The SIWE message format is invalid.")
