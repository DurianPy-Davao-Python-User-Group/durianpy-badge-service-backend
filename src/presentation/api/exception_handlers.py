"""FastAPI exception handlers preventing stack traces and information leakage."""

import traceback
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.logging import logger
from src.domain.exceptions.base_exceptions import (
    DomainError,
    EntityNotFoundError,
    EntityValidationError,
    RepositoryError,
    StorageServiceError,
)


def register_domain_exception_handlers(app: FastAPI) -> None:
    """
    Register global FastAPI exception handlers for domain and generic exceptions.

    Translates domain boundary and unhandled system exceptions into sanitized,
    consistent HTTP error envelopes while ensuring internal stack traces, system paths,
    and database error details are never leaked to API clients.

    :param app: FastAPI application instance.
    :type app: FastAPI
    """

    @app.exception_handler(EntityNotFoundError)
    async def entity_not_found_handler(request: Request, exc: EntityNotFoundError) -> JSONResponse:
        logger.warning(f'Resource not found on {request.method} {request.url.path}: {exc.message}')
        return JSONResponse(
            status_code=HTTPStatus.NOT_FOUND.value,
            content={
                'error': {
                    'code': exc.code,
                    'message': exc.message,
                }
            },
        )

    @app.exception_handler(EntityValidationError)
    async def entity_validation_handler(request: Request, exc: EntityValidationError) -> JSONResponse:
        logger.warning(f'Domain validation error on {request.method} {request.url.path}: {exc.message}')
        return JSONResponse(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY.value,
            content={
                'error': {
                    'code': exc.code,
                    'message': exc.message,
                }
            },
        )

    @app.exception_handler(RepositoryError)
    async def repository_error_handler(request: Request, exc: RepositoryError) -> JSONResponse:
        logger.error(f'Persistence repository failure on {request.method} {request.url.path}: {exc.message}')
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
            content={
                'error': {
                    'code': exc.code,
                    'message': 'A database persistence error occurred while processing your request.',
                }
            },
        )

    @app.exception_handler(StorageServiceError)
    async def storage_service_error_handler(request: Request, exc: StorageServiceError) -> JSONResponse:
        logger.error(f'Storage service failure on {request.method} {request.url.path}: {exc.message}')
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
            content={
                'error': {
                    'code': exc.code,
                    'message': 'A storage or media asset resolution error occurred.',
                }
            },
        )

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        logger.warning(f'Domain error on {request.method} {request.url.path}: {exc.message}')
        return JSONResponse(
            status_code=HTTPStatus.BAD_REQUEST.value,
            content={
                'error': {
                    'code': exc.code,
                    'message': exc.message,
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        logger.warning(f'HTTP exception {exc.status_code} on {request.method} {request.url.path}: {exc.detail}')
        return JSONResponse(
            status_code=exc.status_code,
            content={
                'error': {
                    'code': 'HTTP_EXCEPTION',
                    'message': str(exc.detail),
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.warning(f'Request schema validation error on {request.method} {request.url.path}: {exc.errors()}')
        return JSONResponse(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY.value,
            content={
                'error': {
                    'code': 'REQUEST_VALIDATION_ERROR',
                    'message': 'Request validation failed.',
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all handler ensuring unhandled exceptions and tracebacks are never exposed."""
        tb_str = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        logger.error(f'Unhandled internal server exception on {request.method} {request.url.path}:\n{tb_str}')
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
            content={
                'error': {
                    'code': 'INTERNAL_SERVER_ERROR',
                    'message': 'An unexpected internal server error occurred.',
                }
            },
        )
