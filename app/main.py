from fastapi import APIRouter, FastAPI

from . import VERSION
from .routers import about, auth, default

app = FastAPI(
    title="Safe Auth Service",
    description="API to grant JWT tokens for using across the Safe Core{API} infrastructure.",
    version=VERSION,
    docs_url=None,
    redoc_url=None,
)

# Router configuration
api_v1_router = APIRouter(
    prefix="/api/v1",
)
api_v1_router.include_router(about.router)
api_v1_router.include_router(auth.router)
app.include_router(api_v1_router)
app.include_router(default.router)
