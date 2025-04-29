from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str


class PreRegistrationUser(BaseModel):
    email: EmailStr


class PreRegistrationResponse(BaseModel):
    token: str


class RegistrationUser(PreRegistrationUser):
    token: str
    password: str


class RegistrationUserResponse(PreRegistrationUser):
    uuid: str


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1)
    new_password: str = Field(min_length=1)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    token: str
    new_password: str = Field(min_length=1)
