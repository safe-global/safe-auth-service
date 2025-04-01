from fastapi import APIRouter, HTTPException

from starlette import status

from ..models.users import (
    PreRegistrationResponse,
    PreRegistrationUser,
    RegistrationUser,
    RegistrationUserResponse,
)
from ..services.registration_service import (
    TemporaryTokenExists,
    TemporaryTokenNotValid,
    pre_register_user,
    register_user,
)

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "/pre-registrations",
    response_model=PreRegistrationResponse,
)
async def pre_register(user_request: PreRegistrationUser) -> PreRegistrationResponse:
    try:
        token = pre_register_user(str(user_request.email))
        return PreRegistrationResponse(token=token)
    except TemporaryTokenExists as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.post(
    "/registrations",
    response_model=RegistrationUserResponse,
)
async def register(user_request: RegistrationUser) -> RegistrationUserResponse:
    try:
        user_uuid = await register_user(
            str(user_request.email),
            user_request.password,
            user_request.token,
        )
        return RegistrationUserResponse(email=user_request.email, uuid=user_uuid)
    except TemporaryTokenNotValid as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
