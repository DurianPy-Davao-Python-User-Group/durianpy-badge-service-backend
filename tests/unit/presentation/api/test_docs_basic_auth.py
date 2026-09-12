"""Unit tests for Swagger UI and OpenAPI documentation Basic Auth and visibility policies."""

import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.core.settings import Environment, settings
from src.presentation.api.main import app


def test_docs_in_production_returns_404() -> None:
    """Verify documentation endpoints return 404 Not Found in production environment."""
    client = TestClient(app)
    with patch.object(settings, 'ENVIRONMENT', Environment.PRODUCTION):
        res_docs = client.get('/docs')
        assert res_docs.status_code == 404

        res_openapi = client.get('/openapi.json')
        assert res_openapi.status_code == 404


def test_docs_local_development_allows_unauthenticated_access() -> None:
    """Verify documentation endpoints are freely accessible without credentials during local development."""
    client = TestClient(app)
    with patch.dict(os.environ, {}, clear=True):
        with patch.object(settings, 'ENVIRONMENT', Environment.DEVELOPMENT):
            with patch.object(settings, 'ENABLE_SWAGGER_BASIC_AUTH', False):
                res_docs = client.get('/docs')
                assert res_docs.status_code == 200
                assert 'Swagger UI' in res_docs.text

                res_openapi = client.get('/openapi.json')
                assert res_openapi.status_code == 200
                assert 'openapi' in res_openapi.json()


def test_docs_in_cloud_dev_without_credentials_returns_401_challenge() -> None:
    """Verify cloud non-production environment returns 401 with WWW-Authenticate header when credentials missing."""
    client = TestClient(app)
    with patch.dict(os.environ, {'AWS_LAMBDA_FUNCTION_NAME': 'dev-api'}):
        with patch.object(settings, 'ENVIRONMENT', Environment.DEVELOPMENT):
            with patch.object(settings, 'ENABLE_SWAGGER_BASIC_AUTH', True):
                res_docs = client.get('/docs')
                assert res_docs.status_code == 401
                assert 'www-authenticate' in res_docs.headers
                assert res_docs.headers['www-authenticate'] == 'Basic realm="DurianPy Badge System API"'

                res_openapi = client.get('/openapi.json')
                assert res_openapi.status_code == 401
                assert 'www-authenticate' in res_openapi.headers
                assert res_openapi.headers['www-authenticate'] == 'Basic realm="DurianPy Badge System API"'


def test_docs_in_cloud_dev_with_invalid_credentials_returns_401_challenge() -> None:
    """Verify cloud non-production environment returns 401 with WWW-Authenticate header on invalid credentials."""
    client = TestClient(app)
    with patch.dict(os.environ, {'AWS_LAMBDA_FUNCTION_NAME': 'dev-api'}):
        with patch.object(settings, 'ENVIRONMENT', Environment.DEVELOPMENT):
            with patch.object(settings, 'ENABLE_SWAGGER_BASIC_AUTH', True):
                with patch.object(settings, 'SWAGGER_BASIC_AUTH_USERNAME', 'durianpy-dev'):
                    with patch.object(settings, 'SWAGGER_BASIC_AUTH_PASSWORD', 'secret-pw'):
                        res_docs = client.get('/docs', auth=('durianpy-dev', 'wrong-pw'))
                        assert res_docs.status_code == 401
                        assert res_docs.headers['www-authenticate'] == 'Basic realm="DurianPy Badge System API"'

                        res_openapi = client.get('/openapi.json', auth=('wrong-user', 'secret-pw'))
                        assert res_openapi.status_code == 401
                        assert res_openapi.headers['www-authenticate'] == 'Basic realm="DurianPy Badge System API"'


def test_docs_in_cloud_dev_with_valid_credentials_returns_200_ok() -> None:
    """Verify cloud non-production environment returns 200 OK when valid credentials are provided."""
    client = TestClient(app)
    with patch.dict(os.environ, {'AWS_LAMBDA_FUNCTION_NAME': 'dev-api'}):
        with patch.object(settings, 'ENVIRONMENT', Environment.DEVELOPMENT):
            with patch.object(settings, 'ENABLE_SWAGGER_BASIC_AUTH', True):
                with patch.object(settings, 'SWAGGER_BASIC_AUTH_USERNAME', 'durianpy-dev'):
                    with patch.object(settings, 'SWAGGER_BASIC_AUTH_PASSWORD', 'secret-pw'):
                        res_docs = client.get('/docs', auth=('durianpy-dev', 'secret-pw'))
                        assert res_docs.status_code == 200
                        assert 'Swagger UI' in res_docs.text

                        res_openapi = client.get('/openapi.json', auth=('durianpy-dev', 'secret-pw'))
                        assert res_openapi.status_code == 200
                        assert 'openapi' in res_openapi.json()
