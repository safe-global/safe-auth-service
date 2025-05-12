import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyInfo(BaseModel):
    description: str = Field(max_length=200)


class ApiKeyPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created: datetime.datetime
    key: str
    description: str
