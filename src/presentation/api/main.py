"""Main API application entrypoint defining FastAPI routes and ASGI handlers."""

from contextlib import asynccontextmanager
from http import HTTPStatus
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.infrastructure.db.mock_dynamodb import ensure_mock_database
from src.presentation.api.exception_handlers import (
    register_domain_exception_handlers,
)
from src.presentation.api.routes.main_controller import api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context initializing mock database if needed."""
    ensure_mock_database()
    yield


app = FastAPI(
    title='DurianPy Badge System API',
    lifespan=lifespan,
)

register_domain_exception_handlers(app)
app.include_router(api_router)


@app.get('/health', include_in_schema=False)
def healthcheck():
    """
    Health check endpoint returning application status.

    :returns: JSON response with HTTP 200 OK phrase and status code.
    :rtype: JSONResponse
    """
    return JSONResponse(HTTPStatus.OK.phrase, status_code=HTTPStatus.OK.value)
