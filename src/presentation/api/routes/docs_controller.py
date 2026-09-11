"""API documentation route controller serving protected Swagger UI and OpenAPI schema."""

import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from src.core.settings import Environment, settings

router = APIRouter(include_in_schema=False)

__security = HTTPBasic(auto_error=False)


def __verify_docs_credentials(
    credentials: Optional[HTTPBasicCredentials] = Depends(__security),
) -> None:
    """
    Validate HTTP Basic Auth credentials for API documentation endpoints.

    In production environment, raises 404 Not Found to prevent discovery.
    In local development environment or when basic auth is disabled, allows access without credentials.
    In cloud non-production environments, enforces Basic Auth with WWW-Authenticate challenge.

    :param credentials: Provided HTTP Basic authentication credentials.
    :type credentials: Optional[HTTPBasicCredentials]
    :raises HTTPException: 404 in production, or 401 when authentication fails with WWW-Authenticate header.
    """
    if settings.ENVIRONMENT == Environment.PRODUCTION:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Not Found',
        )

    if settings.is_local or not settings.ENABLE_SWAGGER_BASIC_AUTH:
        return

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Unauthorized',
            headers={'WWW-Authenticate': 'Basic realm="DurianPy Badge System API"'},
        )

    is_user_correct = secrets.compare_digest(
        credentials.username,
        settings.SWAGGER_BASIC_AUTH_USERNAME,
    )
    is_pass_correct = secrets.compare_digest(
        credentials.password,
        settings.SWAGGER_BASIC_AUTH_PASSWORD,
    )

    if not (is_user_correct and is_pass_correct):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Unauthorized',
            headers={'WWW-Authenticate': 'Basic realm="DurianPy Badge System API"'},
        )


@router.get('/docs', include_in_schema=False)
def get_swagger_documentation(
    request: Request,
    _: None = Depends(__verify_docs_credentials),
) -> HTMLResponse:
    """
    Serve interactive Swagger UI documentation protected by Basic Auth.

    :param request: Incoming HTTP request instance.
    :type request: Request
    :param _: Verified documentation credentials dependency.
    :type _: None
    :returns: Rendered Swagger UI HTML response.
    :rtype: HTMLResponse
    """
    return get_swagger_ui_html(
        openapi_url='/openapi.json',
        title=f'{request.app.title} - Swagger UI',
    )


@router.get('/openapi.json', include_in_schema=False)
def get_openapi_schema(
    request: Request,
    _: None = Depends(__verify_docs_credentials),
) -> JSONResponse:
    """
    Serve OpenAPI JSON schema definition protected by Basic Auth.

    :param request: Incoming HTTP request instance.
    :type request: Request
    :param _: Verified documentation credentials dependency.
    :type _: None
    :returns: OpenAPI JSON schema response.
    :rtype: JSONResponse
    """
    return JSONResponse(
        get_openapi(
            title=request.app.title,
            version=request.app.version,
            routes=request.app.routes,
        )
    )
