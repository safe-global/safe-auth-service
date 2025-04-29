import uuid
from unittest import mock

import faker

from ...datasources.db.connector import db_session_context
from ...datasources.db.models import User
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

    @db_session_context
    async def test_change_password(self):
        user, old_password = await generate_random_user()
        user_service = UserService()
        self.assertTrue(
            user_service.verify_password(old_password, user.hashed_password)
        )

        new_password = fake.password()
        wrong_old_password = fake.password()
        with self.assertRaises(WrongPassword):
            await user_service.change_password(user, wrong_old_password, new_password)

        self.assertTrue(
            await user_service.change_password(user, old_password, new_password)
        )
        # Get user from database again
        updated_user = await User.get_by_user_id(user.id)
        assert updated_user is not None
        self.assertFalse(
            user_service.verify_password(old_password, updated_user.hashed_password)
        )
        self.assertTrue(
            user_service.verify_password(new_password, updated_user.hashed_password)
        )

    @db_session_context
    async def test_forgot_password(self):
        user, _ = await generate_random_user()
        user_service = UserService()
        with mock.patch("app.services.user_service.send_reset_password_temporary_token_email") as send_reset_password_temporary_token_email:
            await user_service.forgot_password(user.email)
            send_reset_password_temporary_token_email.assert_called_once()

        with self.assertRaises(TemporaryTokenExists):
            await user_service.forgot_password(user.email)

    @db_session_context
    @mock.patch("app.services.user_service.send_reset_password_temporary_token_email")
    async def test_reset_password(self, mock_send_reset_password_temporary_token_email):
        user, old_password = await generate_random_user()
        user_service = UserService()
        await user_service.forgot_password(user.email)
        mock_send_reset_password_temporary_token_email.assert_called_once()
        email, right_token = mock_send_reset_password_temporary_token_email.call_args[0]
        self.assertEqual(user.email, email)
        wrong_token = str(uuid.uuid4())
        new_password = fake.password()

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
