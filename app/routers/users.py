from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from starlette import status

from ..models.users import (
    PreRegistrationResponse,
    PreRegistrationUser,
    RegistrationUser,
    RegistrationUserResponse,
    Token,
)
from ..services.user_service import (
    TemporaryTokenExists,
    TemporaryTokenNotValid,
    UserAlreadyExists,
    UserService,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/users/logins")

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "/pre-registrations",
    response_model=PreRegistrationResponse,
)
async def pre_register(user_request: PreRegistrationUser) -> PreRegistrationResponse:
    user_service = UserService()
    try:
        token = user_service.pre_register_user(user_request.email)
        return PreRegistrationResponse(token=token)
    except TemporaryTokenExists as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.post(
    "/registrations",
    response_model=RegistrationUserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(user_request: RegistrationUser) -> RegistrationUserResponse:
    user_service = UserService()
    try:
        user_uuid = await user_service.register_user(
            user_request.email,
            user_request.password,
            user_request.token,
        )
        return RegistrationUserResponse(email=user_request.email, uuid=user_uuid)
    except (TemporaryTokenNotValid, UserAlreadyExists) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.post("/logins")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    user_service = UserService()
    token = await user_service.login_user(
        form_data.username,
        form_data.password,
    )
    return token


@router.get("/me")
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}
