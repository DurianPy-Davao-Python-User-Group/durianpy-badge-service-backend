"""Main API application entrypoint defining FastAPI routes and ASGI handlers."""

from http import HTTPStatus

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.core.logging import log_execution

app = FastAPI()


@app.get('/health', include_in_schema=False)
@log_execution
def healthcheck():
    """
    Health check endpoint returning application status.

    :returns: JSON response with HTTP 200 OK phrase and status code.
    :rtype: JSONResponse
    """
    return JSONResponse(HTTPStatus.OK.phrase, status_code=HTTPStatus.OK.value)

