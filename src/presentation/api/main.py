"""Main API application entrypoint defining FastAPI routes and ASGI handlers."""

from http import HTTPStatus

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.presentation.api.exception_handlers import (
    register_domain_exception_handlers,
)
from src.presentation.api.routes.main_controller import api_router

app = FastAPI(
    title='DurianPy Badge System API',
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

register_domain_exception_handlers(app)
app.include_router(api_router)


@app.get('/health', include_in_schema=False)
def healthcheck() -> JSONResponse:
    """
    Health check endpoint returning application status.

    :returns: JSON response with HTTP 200 OK phrase and status code.
    :rtype: JSONResponse
    """
    return JSONResponse(HTTPStatus.OK.phrase, status_code=HTTPStatus.OK.value)
