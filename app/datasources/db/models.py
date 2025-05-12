import datetime
import uuid
from typing import Self, Sequence

from sqlalchemy import DateTime, func, update
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


class TimeStampedSQLModel(SQLModel):
    """
    An abstract base class model that provides self-updating
    ``created`` and ``modified`` fields.

    """

    created: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
        sa_type=DateTime(timezone=True),  # type: ignore
        index=True,
    )

    modified: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
        sa_type=DateTime(timezone=True),  # type: ignore
        sa_column_kwargs={
            "onupdate": lambda: datetime.datetime.now(datetime.timezone.utc),
        },
    )


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

    @classmethod
    async def get_by_user_id(cls, user_id: uuid.UUID) -> Self | None:
        result = await db_session.execute(select(cls).where(cls.id == user_id))
        if user := result.first():
            return user[0]
        return None

    @classmethod
    async def update_password(cls, user_id: uuid.UUID, new_password: str) -> bool:
        """
        Update the password for a user.

        Args:
            user_id:
            new_password:

        Returns: True if the password was updated, False otherwise.

        """
        query = (
            update(cls)
            .where(col(cls.id) == user_id)
            .values(hashed_password=new_password)
        )
        result = await db_session.execute(query)
        await db_session.commit()
        return True if result.rowcount == 1 else False


class ApiKey(SqlQueryBase, TimeStampedSQLModel, SQLModel, table=True):
    id: uuid.UUID = Field(primary_key=True)
    user_id: uuid.UUID = Field(nullable=False, foreign_key="user.id")
    key: str = Field(nullable=False, unique=True)
    description: str = Field(nullable=False, max_length=200)

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
        Delete an ApiKey by api key id and user id.

        Args:
            api_key_id:
            user_id:

        Returns: True if deleted False otherwise.

        """
        query = (
            delete(cls)
            .where(col(cls.user_id) == user_id)
            .where(col(cls.id) == api_key_id)
        )
        result = await db_session.execute(query)
        await db_session.commit()
        return True if result.rowcount == 1 else False

    @classmethod
    async def get_api_keys_by_user(cls, user_id: uuid.UUID) -> Sequence["ApiKey"]:
        """
        Get a list of ApiKeys by user id.

        Args:
            user_id:

        Returns: List of ApiKeys.

        """
        query = select(cls).where(cls.user_id == user_id)
        result = await db_session.execute(query)
        return result.scalars().all()
