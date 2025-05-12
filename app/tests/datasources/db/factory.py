import uuid
from typing import Tuple

import faker

from app.datasources.db.models import ApiKey, User
from app.models.types import passwordType
from app.services.user_service import UserService

fake = faker.Faker()


async def generate_random_user() -> Tuple[User, passwordType]:
    """
    Generate a random user with mail and password.
    Returns: User object and plain password

    """
    password = passwordType(fake.password(length=8))
    user_service = UserService()
    user = await User(
        email=fake.email(), hashed_password=user_service.hash_password(password)
    ).create()
    return user, password


async def generate_random_api_key(user_id: uuid.UUID):
    return await ApiKey(
        id=uuid.uuid4(),
        user_id=user_id,
        key=fake.password(100),
        description="Api key for testing",
    ).create()
