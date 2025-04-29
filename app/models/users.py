from pydantic import BaseModel, EmailStr


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
    old_password: str
    new_password: str
