import uuid

import faker

from ...datasources.db.connector import db_session_context
from ...datasources.db.models import User
from ...models.types import passwordType
from ...services.user_service import (
    TemporaryTokenExists,
    TemporaryTokenNotValid,
    UserService,
    WrongPassword,
)
from ..datasources.db.async_db_test_case import AsyncDbTestCase
from ..datasources.db.factory import generate_random_user

fake = faker.Faker()


class TestApiKeyService(AsyncDbTestCase):

    def setUp(self):
        self.user_service = UserService()

    @db_session_context
    async def test_change_password(self):
        user, old_password = await generate_random_user()
        self.assertTrue(
            self.user_service.verify_password(old_password, user.hashed_password)
        )

        new_password = passwordType(fake.password())
        wrong_old_password = passwordType(fake.password())
        with self.assertRaises(WrongPassword):
            await self.user_service.change_password(
                user, wrong_old_password, new_password
            )

        self.assertTrue(
            await self.user_service.change_password(user, old_password, new_password)
        )
        # Get user from database again
        updated_user = await User.get_by_user_id(user.id)
        assert updated_user is not None
        self.assertFalse(
            self.user_service.verify_password(
                old_password, updated_user.hashed_password
            )
        )
        self.assertTrue(
            self.user_service.verify_password(
                new_password, updated_user.hashed_password
            )
        )

    @db_session_context
    async def test_forgot_password(self):
        user_service = UserService()
        self.assertIsNone(await user_service.get_forgot_password_token(fake.email()))

        user, _ = await generate_random_user()
        self.assertIsNotNone(await user_service.get_forgot_password_token(user.email))

        with self.assertRaises(TemporaryTokenExists):
            await user_service.get_forgot_password_token(user.email)

    @db_session_context
    async def test_reset_password(self):
        user, old_password = await generate_random_user()
        user_service = UserService()
        right_token = await user_service.get_forgot_password_token(user.email)
        assert right_token is not None
        self.assertEqual(user.email, user.email)
        wrong_token = str(uuid.uuid4())
        new_password = passwordType(fake.password())

        with self.assertRaises(TemporaryTokenNotValid):
            await user_service.reset_password(user.email, wrong_token, new_password)

        self.assertFalse(
            user_service.verify_password(new_password, user.hashed_password)
        )
        self.assertTrue(
            await user_service.reset_password(user.email, right_token, new_password)
        )
        updated_user = await User.get_by_user_id(user.id)
        assert updated_user is not None
        self.assertTrue(
            user_service.verify_password(new_password, updated_user.hashed_password)
        )

    @db_session_context
    async def test_login_or_register(self):
        self.assertEqual(await User.count(), 0)
        random_email = "random@safe.global"
        # Email must be registered
        token = await self.user_service.login_or_register(random_email)
        self.assertEqual(await User.count(), 1)
        self.assertIsNotNone(token.access_token)
        self.assertEqual(token.token_type, "bearer")

        # Login after register
        token_2 = await self.user_service.login_or_register(random_email)
        self.assertEqual(await User.count(), 1)
        self.assertIsNotNone(token.access_token)
        self.assertEqual(token.token_type, "bearer")
        self.assertNotEqual(token_2.access_token, token.access_token)
