from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from starlette import status

from ..datasources.email.email_client import (
    send_register_temporary_token_email,
    send_reset_password_temporary_token_email,
)
from ..models.users import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    PreRegistrationResponse,
    PreRegistrationUser,
    RegistrationUser,
    RegistrationUserResponse,
    ResetPasswordRequest,
    Token,
)
from ..services.user_service import (
    TemporaryTokenExists,
    TemporaryTokenNotValid,
    UserAlreadyExists,
    UserService,
)
from .auth import get_jwt_info_from_auth_token, get_user_from_jwt

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "/pre-registrations",
    response_model=PreRegistrationResponse,
)
async def pre_register(
    user_request: PreRegistrationUser, background_tasks: BackgroundTasks
) -> PreRegistrationResponse:
    user_service = UserService()
    try:
        token = user_service.pre_register_user(user_request.email)
        background_tasks.add_task(
            send_register_temporary_token_email, user_request.email, token
        )
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


@router.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    user_service = UserService()
    token = await user_service.login_user(
        form_data.username,
        form_data.password,
    )
    return token


@router.get("/me")
async def get_current_user(
    jwt_info: Annotated[dict, Depends(get_jwt_info_from_auth_token)],
):
    return jwt_info


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    change_password_request: ChangePasswordRequest,
    jwt_info: Annotated[dict, Depends(get_jwt_info_from_auth_token)],
):
    user = await get_user_from_jwt(jwt_info)
    user_service = UserService()
    await user_service.change_password(
        user,
        change_password_request.old_password,
        change_password_request.new_password,
    )


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
async def forgot_password(
    forgot_password_request: ForgotPasswordRequest, background_tasks: BackgroundTasks
):
    user_service = UserService()
    token = await user_service.get_forgot_password_token(forgot_password_request.email)
    if token:
        background_tasks.add_task(
            send_reset_password_temporary_token_email,
            forgot_password_request.email,
            token,
        )


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(reset_password_request: ResetPasswordRequest):
    user_service = UserService()
    await user_service.reset_password(
        reset_password_request.email,
        reset_password_request.token,
        reset_password_request.new_password,
    )
