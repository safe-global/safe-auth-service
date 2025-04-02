import faker

from app.datasources.db.connector import db_session_context
from app.datasources.db.models import Users

from .async_db_test_case import AsyncDbTestCase

fake = faker.Faker()


class TestModel(AsyncDbTestCase):

    @db_session_context
    async def test_contract(self):
        contract = Users(email=fake.email(), hashed_password=fake.password())
        await contract.create()
        result = await contract.get_all()
        self.assertEqual(result[0], contract)
