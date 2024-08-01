from datetime import UTC, datetime, timedelta

from siwe.siwe import ISO8601Datetime, SiweMessage, VersionEnum

from gnosis.eth.utils import fast_to_checksum_address

from ..config import settings
from .nonce_service import generate_nonce


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
        valid_until=ISO8601Datetime.from_datetime(
            datetime.now(UTC) + timedelta(seconds=settings.NONCE_TTL_SECONDS)
        ),
    )

    return message.prepare_message()
