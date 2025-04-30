from pydantic import BaseModel, EmailStr, Field, SecretStr

from typing_extensions import Annotated

passwordType = Annotated[SecretStr, Field(min_length=8)]


class Token(BaseModel):
    access_token: str
    token_type: str


class PreRegistrationUser(BaseModel):
    email: EmailStr


class PreRegistrationResponse(BaseModel):
    token: str


class RegistrationUser(PreRegistrationUser):
    token: str
    password: passwordType


class RegistrationUserResponse(PreRegistrationUser):
    uuid: str


class ChangePasswordRequest(BaseModel):
    old_password: passwordType
    new_password: passwordType


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    token: str
    new_password: passwordType
