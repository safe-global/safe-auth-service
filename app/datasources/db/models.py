import datetime
import uuid
from typing import Self

from sqlalchemy import DateTime, func
from sqlmodel import Field, SQLModel, col, delete, select

from .connector import db_session


class SqlQueryBase:

    @classmethod
    async def get_all(cls):
        result = await db_session.execute(select(cls))
        return result.scalars().all()

    async def _save(self):
        db_session.add(self)
        await db_session.commit()
        return self

    async def update(self):
        return await self._save()

    async def create(self):
        return await self._save()


class User(SqlQueryBase, SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(nullable=False, index=True, unique=True)
    hashed_password: str = Field(nullable=False)

    @classmethod
    async def count(cls) -> int:
        return (await db_session.execute(select(func.count(col(cls.id))))).one()[0]

    @classmethod
    async def get_by_email(cls, email: str) -> Self | None:
        result = await db_session.execute(select(cls).where(cls.email == email))
        if user := result.first():
            return user[0]
        return None

class ApiKey(SqlQueryBase, SQLModel, table=True):
    id: uuid.UUID = Field(primary_key=True)
    user_id: uuid.UUID = Field(nullable=False, foreign_key="user.id")
    created_at: datetime.datetime = Field(
        nullable=False, sa_type=DateTime(timezone=True)  # type: ignore
    )
    token: str = Field(nullable=False)

    @classmethod
    async def get_by_ids(cls, api_key_id: uuid.UUID, user_id: uuid.UUID):
        """
        Get an ApiKey by api key id and user id.

        Args:
            api_key_id:
            user_id:

        Returns: ApiKey instance.

        """
        query = select(cls).where(cls.user_id == user_id).where(cls.id == api_key_id)
        result = await db_session.execute(query)

        if api_key := result.scalars().first():
            return api_key

        return None

    @classmethod
    async def delete_by_ids(cls, api_key_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """
        Delete an ApiKey by api_key_id and user_id.

        Args:
            api_key_id:
            user_id:

        Returns: True if deleted false otherwise.

        """
        query = (
            delete(cls)
            .where(col(cls.id) == api_key_id)
            .where(col(cls.user_id) == user_id)
        )
        result = await db_session.execute(query)

        return True if result.rowcount == 1 else False
