from fastapi import APIRouter, HTTPException, Response, status

from app.config import settings

from ..exceptions import (
    InvalidMessageFormatError,
    InvalidNonceError,
    InvalidSignatureError,
)
from ..models import (
    APIErrorResponse,
    JwtToken,
    Nonce,
    SiweMessage,
    SiweMessageRequest,
    SiweMessageVerificationRequest,
)
from ..services.jwt_service import create_jwt_token
from ..services.message_service import (
    create_siwe_message,
    get_siwe_message_info,
    verify_siwe_message,
)
from ..services.nonce_service import generate_nonce

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.get("/nonce", response_model=Nonce)
async def get_nonce() -> "Nonce":
    return Nonce(nonce=generate_nonce())


@router.post("/messages", response_model=SiweMessage)
async def request_siwe_message(
    siwe_message_request: SiweMessageRequest,
) -> "SiweMessage":
    siwe_message = create_siwe_message(
        domain=siwe_message_request.domain,
        address=siwe_message_request.address,
        chain_id=siwe_message_request.chain_id,
        uri=str(siwe_message_request.uri),
        statement=siwe_message_request.statement,
    )
    return SiweMessage(message=siwe_message)


@router.post(
    "/messages/verify",
    response_model=JwtToken,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": APIErrorResponse,
            "description": "The SIWE message format is invalid",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": APIErrorResponse,
            "description": "The SIWE signature is invalid",
        },
    },
)
async def request_auth_token(
    siwe_message_request: SiweMessageVerificationRequest, response: Response
) -> JwtToken:
    try:
        verify_siwe_message(
            message=siwe_message_request.message,
            signature=siwe_message_request.signature,
        )
    except InvalidMessageFormatError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InvalidNonceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InvalidSignatureError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    siwe_message_info = get_siwe_message_info(siwe_message_request.message)
    token = create_jwt_token(siwe_message_info)

    response.set_cookie(
        key=settings.JWT_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.JWT_EXPIRATION_SECONDS,
    )
    return JwtToken(token=token)
