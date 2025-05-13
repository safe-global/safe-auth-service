import datetime
import uuid
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class WebhookEventType(str, Enum):
    SEND_CONFIRMATIONS = ("SEND_CONFIRMATIONS",)
    SEND_MULTISIG_TXS = ("SEND_MULTISIG_TXS",)
    SEND_ETHER_TRANSFERS = ("SEND_ETHER_TRANSFERS",)
    SEND_TOKEN_TRANSFERS = ("SEND_TOKEN_TRANSFERS",)
    SEND_MODULE_TXS = ("SEND_MODULE_TXS",)
    SEND_SAFE_CREATIONS = ("SEND_SAFE_CREATIONS",)
    SEND_MESSAGES = ("SEND_MESSAGES",)
    SEND_REORGS = ("SEND_REORGS",)
    SEND_DELEGATES = "SEND_DELEGATES"


class WebhookEventOption(BaseModel):
    name: str


class WebhookEventsService(BaseModel):
    id: uuid.UUID
    url: str
    authorization: str | None
    chains: list[int]
    events: list[WebhookEventType]
    active: bool


class WebhookRequest(BaseModel):
    description: str | None = Field(default=None, max_length=200)
    url: str = Field(max_length=300)
    authorization: str | None = Field(default=None)
    chains: list[int] = Field(min_length=0)
    events: list[WebhookEventType]
    active: bool = Field(default=True)


class WebhookPublicPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created: datetime.datetime
    updated: datetime.datetime
    description: str | None
    url: str
    authorization: str | None
    chains: list[int]
    events: list[WebhookEventType]
    active: bool
