from typing import Any, Literal

from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .version import VERSION

app = FastAPI(
    title="Safe Auth Service",
    version=VERSION,
    docs_url=None,
    redoc_url=None,
)
app.mount("/static", StaticFiles(directory="static"), name="static")


class About(BaseModel):
    version: str


@app.get("/docs", include_in_schema=False)
async def swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=str(app.openapi_url),
        title=app.title + " - Swagger UI",
        swagger_favicon_url="/static/favicon.ico",
    )


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=str(app.openapi_url),
        title=app.title + " - ReDoc",
        redoc_js_url="https://unpkg.com/redoc@next/bundles/redoc.standalone.js",
        redoc_favicon_url="/static/favicon.ico",
    )


@app.get("/", include_in_schema=False)
async def home() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/v1/about", response_model=About)
async def about() -> Any:
    return {"version": VERSION}


@app.get("/health")
async def health() -> Literal["OK"]:
    return "OK"
