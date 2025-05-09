import logging
import secrets
import uuid
from datetime import timedelta
from typing import cast

from fastapi import HTTPException
from pydantic import SecretStr

import bcrypt
from starlette import status

from ..config import settings
from ..datasources.api_gateway.apisix.apisix_client import get_apisix_client
from ..datasources.cache.redis import get_redis
from ..datasources.db.models import User
from ..models.types import passwordType
from ..models.users import Token
from .jwt_service import JwtService


class UserServiceException(Exception):
    pass


class TemporaryTokenNotValid(UserServiceException):
    pass


class UserAlreadyExists(UserServiceException):
    pass


class UserNotFound(UserServiceException):
    pass


class TemporaryTokenExists(UserServiceException):
    pass


class WrongPassword(UserServiceException):
    pass


class UserDoesNotExist(UserServiceException):
    pass


class UserService:
    TEMPORARY_TOKEN_REGISTRATION_PREFIX = "temporary-token:registrations:"
    TEMPORARY_TOKEN_RESET_PASSWORD_PREFIX = "temporary-token:reset-password:"

    def __init__(self):
        self.jwt_service = JwtService()

    async def create_user_in_db(
        self, user_id: uuid.UUID, email: str, password: passwordType
    ) -> User:
        """
        Creates a new user in the database with a hashed password.

        Args:
            user_id: The unique identifier to assign to the user.
            email: The user's email address.
            password: The user's plain-text password.

        Returns:
            User: The newly created user instance.
        """
        hashed_password = self.hash_password(password)
        user = User(id=user_id, email=email, hashed_password=hashed_password)
        await user.create()
        return user

    async def register_user_in_apisix(self, user_id: uuid.UUID) -> None:
        """
        Registers a new user in APISIX by creating a consumer group and applying rate limits.

        Args:
            user_id (uuid.UUID): The UUID of the user.
        """
        apisix_client = get_apisix_client()
        consumer_group_id = user_id.hex
        await apisix_client.add_consumer_group(consumer_group_id)
        await apisix_client.set_rate_limit_to_consumer_group(
            consumer_group_id,
            settings.APISIX_FREEMIUM_CONSUMER_GROUP_REQUESTS_PER_SECOND_MAX,
            settings.APISIX_FREEMIUM_CONSUMER_GROUP_REQUESTS_PER_SECOND_TIME_WINDOW_SECONDS,
        )

    def emit_access_token(self, user_id: uuid.UUID) -> Token:
        access_token_expires = timedelta(days=settings.JWT_AUTH_SERVICE_EXPIRE_DAYS)
        access_token = self.jwt_service.create_access_token(
            user_id.hex, access_token_expires, settings.JWT_AUDIENCE, {}
        )
        return Token(access_token=access_token, token_type="bearer")

    def verify_password(
        self, plain_password: passwordType, hashed_password: str
    ) -> bool:
        return bcrypt.checkpw(
            plain_password.get_secret_value().encode(), hashed_password.encode()
        )

    def hash_password(self, password: passwordType) -> str:
        """
        Args:
            password:

        Returns:
            A string like '$2b$12$yadYxE5ZNfF28M.M00gha.SEaPF2Z.ICEqgIhbhZrgCrCR7PEK7uS'
        """
        return bcrypt.hashpw(
            password.get_secret_value().encode(), bcrypt.gensalt()
        ).decode()

    def temporary_token_generate(
        self,
        key_prefix: str,
        email: str,
        ttl_seconds: int = settings.PRE_REGISTRATION_TOKEN_TTL_SECONDS,
    ) -> str:
        """
        Generates a temporary token and stores it in the cache for an email

        Returns:
            Temporary token
        """
        token = uuid.uuid4().hex
        get_redis().set(key_prefix + email, token, ex=ttl_seconds)
        return token

    def temporary_token_is_valid(self, key_prefix: str, email: str, token: str) -> bool:
        """
        Checks whether a temporary token is valid for a given email

        Returns:
            `True` if the token is valid
        """
        cached_token = cast(bytes, get_redis().get(key_prefix + email))
        return bool(cached_token and cached_token.decode() == token)

    def temporary_token_exists(self, key_prefix: str, email: str) -> bool:
        """
        Args:
            email:

        Returns:
            ``True`` if a temporary token exists for the provided email
        """
        return cast(bool, get_redis().exists(key_prefix + email))

    def pre_register_user(self, email: str) -> str:
        """
        Args:
            email:

        Returns:
            A temporary token that can be used to register a new user.

        Raises:
            TemporaryTokenExists: if a temporary token already exists for the email
        """

        if self.temporary_token_exists(self.TEMPORARY_TOKEN_REGISTRATION_PREFIX, email):
            raise TemporaryTokenExists(f"Temporary token exists for {email}")
        token = self.temporary_token_generate(
            self.TEMPORARY_TOKEN_REGISTRATION_PREFIX, email
        )
        return token

    async def register_user(
        self, email: str, password: passwordType, token: str
    ) -> uuid.UUID:
        """
        Args:
            email:
            password:
            token: Temporary token generated by `pre_register_user`

        Returns:
            UUID4 of the registered user

        Raises:
            TemporaryTokenNotValid: if the temporary token is not valid
            UserAlreadyExists: user with the provided email exists in the database
        """

        if not self.temporary_token_is_valid(
            self.TEMPORARY_TOKEN_REGISTRATION_PREFIX, email, token
        ):
            raise TemporaryTokenNotValid(f"Temporary token not valid for {email}")
        if await User.get_by_email(email):
            raise UserAlreadyExists(f"User with email {email} already exists")
        user_id = uuid.uuid4()
        await self.register_user_in_apisix(user_id)
        await self.create_user_in_db(user_id, email, password)
        return user_id

    async def authenticate_user(
        self, email: str, password: passwordType
    ) -> User | None:
        user = await User.get_by_email(email)
        if user and self.verify_password(password, user.hashed_password):
            return user
        return None

    async def login_user(self, email: str, password: passwordType) -> Token:
        user = await self.authenticate_user(email, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return self.emit_access_token(user.id)

    async def login_or_register(self, email: str) -> Token:
        """
        For Oauth2 3rd party services (like Google login), force login or register with just the email

        Args:
            email:

        Returns:
            JWT token
        """
        user = await User.get_by_email(email)
        if not user:
            random_password = SecretStr(
                secrets.token_hex(64)
            )  # Random password so user can change it afterward
            user_id = uuid.uuid4()
            await self.register_user_in_apisix(user_id)
            user = await self.create_user_in_db(user_id, email, random_password)
        return self.emit_access_token(user.id)

    async def change_password(
        self, user: User, old_password: passwordType | None, new_password: passwordType
    ) -> bool:
        """
        Changes the password to the provided user.
        If old_password is provided, the password will be checked against the old_password.

        Args:
            user: User instance
            old_password: Old password
            new_password: Password to update

        Returns: True if the password was changed or False otherwise.

        Raises:
            WrongPassword: in case the old password is incorrect

        """
        if old_password is not None and not self.verify_password(
            old_password, user.hashed_password
        ):
            raise WrongPassword("Incorrect password")

        hashed_password = self.hash_password(new_password)
        return await User.update_password(user.id, hashed_password)

    async def get_forgot_password_token(self, email: str) -> str | None:
        """
        Return the temporary token for a provided email.

        Args:
            email:

        Returns: a token if the email exists, None otherwise

        """
        if self.temporary_token_exists(
            self.TEMPORARY_TOKEN_RESET_PASSWORD_PREFIX, email
        ):
            raise TemporaryTokenExists(f"Temporary token exists for {email}")
        # Check if the user exists
        if not await User.get_by_email(email):
            return None

        token = self.temporary_token_generate(
            self.TEMPORARY_TOKEN_RESET_PASSWORD_PREFIX, email
        )
        return token

    async def reset_password(
        self, email: str, token: str, new_password: passwordType
    ) -> bool:
        """
        Changes a password for a user with the provided password.
        Checks that the email was verified from the provided token.

        Args:
            email:
            token:
            new_password:

        Returns:

        """
        if not self.temporary_token_is_valid(
            self.TEMPORARY_TOKEN_RESET_PASSWORD_PREFIX, email, token
        ):
            raise TemporaryTokenNotValid(f"Temporary token not valid for {email}")

        user = await User.get_by_email(email)
        if not user:
            logging.critical(
                f"User for reset password token ({token}) does not exist in the database."
            )
            raise UserDoesNotExist(
                f"User for reset password token ({token}) does not exist in the database."
            )

        return await self.change_password(user, None, new_password)
