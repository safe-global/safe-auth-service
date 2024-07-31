from pydantic import BaseModel, constr


class About(BaseModel):
    version: str


class Nonce(BaseModel):
    nonce: constr(min_length=8, pattern=r"^[A-Za-z0-9]{8,}$")  # noqa: F722
