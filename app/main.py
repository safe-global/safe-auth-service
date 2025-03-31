from fastapi import APIRouter, FastAPI

from starlette.requests import Request
from starlette.responses import Response

from . import VERSION
from .datasources.db.connector import db_session, set_database_session_context
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


@app.middleware("http")
async def http_request_middleware(request: Request, call_next):
    """
    Intercepts request and do some actions:
     - Set the database session context for the current request, so the same database session is used across the whole request.

    :param request:
    :param call_next:
    :return:
    """
    with set_database_session_context():

        response: Response | None = None
        try:
            response = await call_next(request)
        except Exception as e:
            raise e
        finally:
            await db_session.remove()

            return response
