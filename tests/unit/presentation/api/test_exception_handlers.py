"""Unit tests for FastAPI domain and unhandled exception handlers."""

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from src.domain.exceptions.badge_design_exceptions import (
    BadgeDesignNotFoundError,
    BadgeDesignQueryError,
    MediaResolutionError,
)
from src.domain.exceptions.base_exceptions import (
    DomainError,
    EntityValidationError,
)
from src.presentation.api.exception_handlers import (
    register_domain_exception_handlers,
)


def test_domain_exception_handlers_translation() -> None:
    """Verify domain exceptions are gracefully converted to HTTP status codes and JSON responses."""
    test_app = FastAPI()
    register_domain_exception_handlers(test_app)

    @test_app.get('/not-found')
    def not_found_route():
        raise BadgeDesignNotFoundError('Badge design with ID 123 was not found.')

    @test_app.get('/validation-error')
    def validation_error_route():
        raise EntityValidationError('Invalid badge design configuration.')

    @test_app.get('/repo-error')
    def repo_error_route():
        raise BadgeDesignQueryError('Low level DynamoDB socket timeout.')

    @test_app.get('/storage-error')
    def storage_error_route():
        raise MediaResolutionError('Failed to connect to CDN.')

    @test_app.get('/domain-error')
    def domain_error_route():
        raise DomainError('Generic business rule failure.')

    @test_app.get('/http-error')
    def http_error_route():
        raise HTTPException(
            status_code=403,
            detail='Forbidden access.',
            headers={'X-Custom-Header': 'test-header'},
        )

    @test_app.get('/unhandled-crash')
    def unhandled_crash_route():
        # Simulate unexpected bug / zero division / memory error
        return 1 / 0

    client = TestClient(test_app, raise_server_exceptions=False)

    # 1. Not Found (404)
    res_404 = client.get('/not-found')
    assert res_404.status_code == 404
    assert res_404.json()['error']['code'] == 'BadgeDesignNotFoundError'
    assert 'Badge design with ID 123' in res_404.json()['error']['message']

    # 2. Validation Error (422)
    res_422 = client.get('/validation-error')
    assert res_422.status_code == 422
    assert res_422.json()['error']['code'] == 'EntityValidationError'

    # 3. Repository Error (500, sanitized message)
    res_500 = client.get('/repo-error')
    assert res_500.status_code == 500
    assert res_500.json()['error']['code'] == 'BadgeDesignQueryError'
    assert 'database persistence error occurred' in res_500.json()['error']['message']
    assert 'DynamoDB' not in res_500.json()['error']['message']  # Infra leak prevented

    # 4. Storage Error (500, sanitized message)
    res_storage = client.get('/storage-error')
    assert res_storage.status_code == 500
    assert res_storage.json()['error']['code'] == 'MediaResolutionError'

    # 5. Generic Domain Error (400)
    res_400 = client.get('/domain-error')
    assert res_400.status_code == 400
    assert res_400.json()['error']['code'] == 'DomainError'

    # 6. HTTP Exception (403 with headers)
    res_http = client.get('/http-error')
    assert res_http.status_code == 403
    assert res_http.json()['error']['code'] == 'HTTP_EXCEPTION'
    assert res_http.json()['error']['message'] == 'Forbidden access.'
    assert res_http.headers['x-custom-header'] == 'test-header'

    # 7. Unhandled Unexpected Exception (500, no stack trace in response)
    res_crash = client.get('/unhandled-crash')
    assert res_crash.status_code == 500
    body = res_crash.json()
    assert body['error']['code'] == 'INTERNAL_SERVER_ERROR'
    assert body['error']['message'] == 'An unexpected internal server error occurred.'
    assert 'Traceback' not in res_crash.text
    assert 'ZeroDivisionError' not in res_crash.text
