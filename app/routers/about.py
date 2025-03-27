from fastapi import APIRouter

from .. import VERSION
from ..models.about import About

router = APIRouter(
    prefix="/about",
    tags=["About"],
)


@router.get("", response_model=About)
async def about() -> About:
    return About(version=VERSION)
