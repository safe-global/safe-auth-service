from typing import Optional

from pydantic import AnyUrl, BaseModel, Field, field_validator

from gnosis.eth.utils import fast_is_checksum_address


class About(BaseModel):
    version: str


class Nonce(BaseModel):
    nonce: str = Field(min_length=8, pattern=r"^[A-Za-z0-9]{8,}$")


class SiweMessageRequest(BaseModel):
    domain: str = Field(pattern="^[^/?#]+$", examples=["domain.com"])
    address: str
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
