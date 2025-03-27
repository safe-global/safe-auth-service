from fastapi import APIRouter

from ..models.users import (
    PreRegistrationResponse,
    PreRegistrationUser,
    RegistrationUser,
    RegistrationUserResponse,
)
from ..services.registration_service import pre_register_user, register_user

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "/pre-registrations",
    response_model=PreRegistrationResponse,
)
async def pre_register(user_request: PreRegistrationUser) -> PreRegistrationResponse:
    token = pre_register_user(str(user_request.email))
    return PreRegistrationResponse(token=token)


@router.post(
    "/registrations",
    response_model=PreRegistrationResponse,
)
async def register(user_request: RegistrationUser) -> RegistrationUserResponse:
    user_uuid = register_user(
        user_request.email, user_request.password, user_request.token
    )
    return RegistrationUserResponse(
        email=user_request.email, username=user_request.username, uuid=user_uuid
    )
