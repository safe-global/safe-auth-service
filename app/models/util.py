from pydantic import BaseModel


class APIErrorResponse(BaseModel):
    detail: str
