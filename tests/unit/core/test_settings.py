"""Unit tests for Settings configuration."""

import os
from unittest.mock import patch

from src.core.settings import Environment, LogLevel, Settings


def test_settings_default_values() -> None:
    """Verify Settings initializes with default values."""
    s = Settings(
        APP_NAME='test-app',
        ENVIRONMENT=Environment.DEVELOPMENT,
        LOG_LEVEL=LogLevel.INFO,
        REGION='ap-southeast-1',
        CLOUDFRONT_URL='https://cdn.example.com',
    )
    assert s.APP_NAME == 'test-app'
    assert s.ENVIRONMENT == Environment.DEVELOPMENT
    assert s.LOG_LEVEL == LogLevel.INFO
    assert s.REGION == 'ap-southeast-1'
    assert s.CLOUDFRONT_URL == 'https://cdn.example.com'
    assert s.DYNAMODB_MAIN_TABLE_NAME == 'dev-test-app-main'
    assert s.ENABLE_SWAGGER_BASIC_AUTH is False
    assert s.SWAGGER_BASIC_AUTH_USERNAME == ''
    assert s.SWAGGER_BASIC_AUTH_PASSWORD == ''
    assert s.is_local is True


def test_settings_environment_override() -> None:
    """Verify environment variables override default settings."""
    env_vars = {
        'APP_NAME': 'custom-app',
        'ENVIRONMENT': 'prod',
        'LOG_LEVEL': 'warning',
        'CLOUDFRONT_URL': 'https://custom-cdn.example.com',
        'ENABLE_SWAGGER_BASIC_AUTH': 'true',
        'SWAGGER_BASIC_AUTH_USERNAME': 'admin',
        'SWAGGER_BASIC_AUTH_PASSWORD': 'secret-password',
    }
    with patch.dict(os.environ, env_vars):
        s = Settings()
        assert s.APP_NAME == 'custom-app'
        assert s.ENVIRONMENT == Environment.PRODUCTION
        assert s.LOG_LEVEL == LogLevel.WARNING
        assert s.CLOUDFRONT_URL == 'https://custom-cdn.example.com'
        assert s.DYNAMODB_MAIN_TABLE_NAME == 'prod-custom-app-main'
        assert s.ENABLE_SWAGGER_BASIC_AUTH is True
        assert s.SWAGGER_BASIC_AUTH_USERNAME == 'admin'
        assert s.SWAGGER_BASIC_AUTH_PASSWORD == 'secret-password'


def test_settings_dynamodb_table_name_explicit_override() -> None:
    """Verify explicit DYNAMODB_MAIN_TABLE_NAME environment variable overrides default format."""
    env_vars = {
        'APP_NAME': 'custom-app',
        'ENVIRONMENT': 'prod',
        'DYNAMODB_MAIN_TABLE_NAME': 'explicit-table-name',
    }
    with patch.dict(os.environ, env_vars):
        s = Settings()
        assert s.DYNAMODB_MAIN_TABLE_NAME == 'explicit-table-name'


def test_settings_is_local_property() -> None:
    """Verify is_local returns False when running inside AWS Lambda and True otherwise."""
    with patch.dict(os.environ, {'AWS_LAMBDA_FUNCTION_NAME': 'my-lambda-func'}):
        s = Settings()
        assert s.is_local is False

    with patch.dict(os.environ, {}, clear=True):
        s = Settings()
        assert s.is_local is True
