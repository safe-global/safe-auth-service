from fastapi import APIRouter

from ..models import Nonce, SiweMessage, SiweMessageRequest
from ..services.message_service import create_siwe_message
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
