from datetime import UTC, datetime, timedelta

import jwt

from app.config import settings
from app.models.siwe_auth import SiweMessageInfo


def create_jwt_token(siwe_message_info: SiweMessageInfo) -> str:
    """
    Creates a JSON Web Token (JWT) based on the provided Sign-In with Ethereum (SIWE) message information.

    :param siwe_message_info: An object of type `SiweMessageInfo`.
    :return: A signed JWT as a string.
    """
    payload = {
        "exp": datetime.now(UTC) + timedelta(seconds=settings.JWT_EXPIRATION_SECONDS),
        "iss": settings.JWT_ISSUER,
        "chain_id": siwe_message_info.chain_id,
        "signer_address": siwe_message_info.signer_address,
    }
    return jwt.encode(payload, settings.JWT_PRIVATE_KEY, algorithm="RS256")
