from pydantic import BaseModel, EmailStr


class PreRegistrationUser(BaseModel):
    email: EmailStr


class PreRegistrationResponse(BaseModel):
    token: str


class RegistrationUser(PreRegistrationUser):
    token: str
    password: str


class RegistrationUserResponse(PreRegistrationUser):
    uuid: str
