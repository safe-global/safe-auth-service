import datetime
import uuid

from pydantic import BaseModel, ConfigDict


class ApiKeyPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created: datetime.datetime
    token: str
