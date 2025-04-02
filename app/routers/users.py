from fastapi import APIRouter, HTTPException

from starlette import status

from ..models.users import (
    PreRegistrationResponse,
    PreRegistrationUser,
    RegistrationUser,
    RegistrationUserResponse,
)
from ..services.user_service import (
    TemporaryTokenExists,
    TemporaryTokenNotValid,
    UserService,
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
    user_service = UserService()
    try:
        token = user_service.pre_register_user(str(user_request.email))
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
    user_service = UserService()
    try:
        user_uuid = await user_service.register_user(
            str(user_request.email),
            user_request.password,
            user_request.token,
        )
        return RegistrationUserResponse(email=user_request.email, uuid=user_uuid)
    except TemporaryTokenNotValid as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
