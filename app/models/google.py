from pydantic import BaseModel


class RedirectUrl(BaseModel):
    url: str
