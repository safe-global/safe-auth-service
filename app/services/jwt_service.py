from datetime import datetime, timedelta, timezone

import jwt

from ..config import settings


class JwtService:
    @staticmethod
    def create_access_token(
        subject: str, expires_delta: timedelta, audience: list[str], data: dict
    ) -> str:
        """
        - The JWT must contain an iss (issuer) claim that has a unique identifier for the entity that issued the JWT.
          This value should match the issuer value of the trust relationship.
        - The JWT must contain a sub (subject) claim that identifies the principal as the subject of the JWT
          (e.g., the user ID). This value should match the subject value of the trust relationship unless
          allow_any_subject is true.
        - The JWT must contain an aud (audience) claim with a value that identifies the authorization server as an
          intended audience. The value should be the OAuth2 Token URL.
        - The JWT must contain an exp (expiration time) claim that restricts the time window during which the JWT can
          be used. This can be controlled through the /oauth2/grant/jwt/max_ttl setting.

        Args:
            subject: identifies the principal as the subject of the JWT (e.g., the user ID).
                This value should match the subject value of the trust relationship unless allow_any_subject is true.
            expires_delta:
            audience: List of services the token can be used in
            data:

        Returns:
            An encoded and signed JWT token.
        """
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode = {
            "iss": settings.JWT_ISSUER,
            "sub": subject,
            "aud": audience,
            "exp": expire,
            "data": data.copy(),
        }
        encoded_jwt = jwt.encode(
            to_encode, settings.JWT_PRIVATE_KEY, algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
