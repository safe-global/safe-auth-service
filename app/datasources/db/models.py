import uuid

from sqlmodel import Field, SQLModel, select

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


class Users(SqlQueryBase, SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(nullable=False, index=True, unique=True)
    hashed_password: str = Field(nullable=False)
