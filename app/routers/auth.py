from fastapi import APIRouter

from ..models import Nonce
from ..siwe.nonce_repository import get_nonce_repository

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.get("/nonce", response_model=Nonce)
async def nonce() -> "Nonce":
    return Nonce(nonce=get_nonce_repository().generate_nonce())
