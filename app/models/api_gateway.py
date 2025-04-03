from typing import Any

from pydantic import BaseModel


class ConsumerGroup(BaseModel):
    name: str
    description: str | None
    labels: dict[str, str] | None
    plugins: dict[str, Any]


class Consumer(BaseModel):
    name: str
    description: str | None
    labels: dict[str, str] | None
    plugins: dict[str, Any] | None
    consumer_group_name: str | None
