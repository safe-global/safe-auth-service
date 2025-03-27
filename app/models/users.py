from pydantic import BaseModel, EmailStr


class About(BaseModel):
    version: str


class PreRegistrationUser(BaseModel):
    email: EmailStr


class PreRegistrationResponse(BaseModel):
    token: str


class RegistrationUser(PreRegistrationUser):
    token: str
    username: str
    password: str


class RegistrationUserResponse(PreRegistrationUser):
    username: str
    uuid: str
