import faker

from ...datasources.db.connector import db_session_context
from ...datasources.db.models import User
from ...services.user_service import UserService, WrongPassword
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
