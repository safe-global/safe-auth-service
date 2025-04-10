import datetime
import uuid

from pydantic import BaseModel


class ApiKeyPublic(BaseModel):
    id: uuid.UUID
    created: datetime.datetime
    token: str

    class Config:
        from_attributes = True
