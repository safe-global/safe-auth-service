import uuid

from pydantic import BaseModel, EmailStr

from app.models.types import passwordType


class Token(BaseModel):
    access_token: str
    token_type: str


class PreRegistrationUser(BaseModel):
    email: EmailStr


class RegistrationUserResponse(PreRegistrationUser):
    uuid: uuid.UUID


class RegistrationUser(BaseModel):
    token: str
    password: passwordType


class ChangePasswordRequest(BaseModel):
    old_password: passwordType
    new_password: passwordType


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: passwordType
