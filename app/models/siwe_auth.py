from typing import Any, Optional

from pydantic import AnyUrl, BaseModel, Field, field_validator

from safe_eth.eth.utils import fast_is_checksum_address


class Nonce(BaseModel):
    nonce: str = Field(min_length=8, pattern=r"^[A-Za-z0-9]{8,}$")


class SiweMessageRequest(BaseModel):
    domain: str = Field(pattern="^[^/?#]+$", examples=["domain.com"])
    address: str = Field(examples=["0xa..."])
    chain_id: int
    uri: AnyUrl
    statement: Optional[str] = Field(default=None)

    @field_validator("address")
    def validate_address(cls, value):
        if not fast_is_checksum_address(value):
            raise ValueError("Invalid Ethereum address")
        return value


class SiweMessage(BaseModel):
    message: str


class SiweMessageInfo(BaseModel):
    chain_id: int
    signer_address: str


class SiweMessageVerificationRequest(BaseModel):
    message: str
    signature: str = Field(
        min_length=132, pattern=r"^0x[a-fA-F0-9]+$", examples=["0xa..."]
    )


class JwtToken(BaseModel):
    token: str


class APIErrorResponse(BaseModel):
    detail: str


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
