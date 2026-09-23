"""Unit tests for Settings configuration."""

import os
from unittest.mock import patch

from src.core.settings import Environment, LogLevel, Settings


def test_settings_default_values() -> None:
    """Verify Settings initializes with default values."""
    s = Settings(
        _env_file=None,
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
    assert s.S3_BUCKET_NAME == 'dev-durianpy-badge-system-bucket'
    assert s.TECHTIX_API_BASE_URL == ''
    assert s.ENABLE_SWAGGER_BASIC_AUTH is False
    assert s.SWAGGER_BASIC_AUTH_USERNAME == ''
    assert s.SWAGGER_BASIC_AUTH_PASSWORD == ''
    assert s.COGNITO_USER_POOL_ID == ''
    assert s.COGNITO_APP_CLIENT_ID == ''
    assert s.cognito_issuer == 'https://cognito-idp.ap-southeast-1.amazonaws.com/'
    assert s.cognito_jwks_url == 'https://cognito-idp.ap-southeast-1.amazonaws.com//.well-known/jwks.json'
    assert s.is_local is True


def test_settings_environment_override() -> None:
    """Verify environment variables override default settings."""
    env_vars = {
        'APP_NAME': 'custom-app',
        'ENVIRONMENT': 'prod',
        'LOG_LEVEL': 'warning',
        'REGION': 'us-east-1',
        'CLOUDFRONT_URL': 'https://custom-cdn.example.com',
        'S3_BUCKET_NAME': 'custom-s3-bucket',
        'TECHTIX_API_BASE_URL': 'https://custom-techtix.example.com',
        'ENABLE_SWAGGER_BASIC_AUTH': 'true',
        'SWAGGER_BASIC_AUTH_USERNAME': 'admin',
        'SWAGGER_BASIC_AUTH_PASSWORD': 'secret-password',
        'COGNITO_USER_POOL_ID': 'ap-southeast-1_TestPool',
        'COGNITO_APP_CLIENT_ID': 'test-client-id-123',
    }
    with patch.dict(os.environ, env_vars):
        s = Settings(_env_file=None)
        assert s.APP_NAME == 'custom-app'
        assert s.ENVIRONMENT == Environment.PRODUCTION
        assert s.LOG_LEVEL == LogLevel.WARNING
        assert s.REGION == 'us-east-1'
        assert s.CLOUDFRONT_URL == 'https://custom-cdn.example.com'
        assert s.DYNAMODB_MAIN_TABLE_NAME == 'prod-custom-app-main'
        assert s.S3_BUCKET_NAME == 'custom-s3-bucket'
        assert s.TECHTIX_API_BASE_URL == 'https://custom-techtix.example.com'
        assert s.ENABLE_SWAGGER_BASIC_AUTH is True
        assert s.SWAGGER_BASIC_AUTH_USERNAME == 'admin'
        assert s.SWAGGER_BASIC_AUTH_PASSWORD == 'secret-password'
        assert s.COGNITO_USER_POOL_ID == 'ap-southeast-1_TestPool'
        assert s.COGNITO_APP_CLIENT_ID == 'test-client-id-123'
        assert s.cognito_issuer == 'https://cognito-idp.us-east-1.amazonaws.com/ap-southeast-1_TestPool'
        assert s.cognito_jwks_url == (
            'https://cognito-idp.us-east-1.amazonaws.com/ap-southeast-1_TestPool/.well-known/jwks.json'
        )


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


def test_settings_s3_bucket_name_default_per_environment() -> None:
    """Verify S3_BUCKET_NAME defaults to {env}-durianpy-badge-system-bucket for different stages."""
    s_dev = Settings(_env_file=None, ENVIRONMENT=Environment.DEVELOPMENT)
    assert s_dev.S3_BUCKET_NAME == 'dev-durianpy-badge-system-bucket'

    s_prod = Settings(_env_file=None, ENVIRONMENT=Environment.PRODUCTION)
    assert s_prod.S3_BUCKET_NAME == 'prod-durianpy-badge-system-bucket'


def test_settings_s3_bucket_name_explicit_override() -> None:
    """Verify explicit S3_BUCKET_NAME environment variable overrides default format."""
    env_vars = {
        'ENVIRONMENT': 'prod',
        'S3_BUCKET_NAME': 'explicit-s3-bucket-name',
    }
    with patch.dict(os.environ, env_vars):
        s = Settings()
        assert s.S3_BUCKET_NAME == 'explicit-s3-bucket-name'


def test_settings_is_local_property() -> None:
    """Verify is_local returns False when running inside AWS Lambda and True otherwise."""
    with patch.dict(os.environ, {'AWS_LAMBDA_FUNCTION_NAME': 'my-lambda-func'}):
        s = Settings()
        assert s.is_local is False

    with patch.dict(os.environ, {}, clear=True):
        s = Settings()
        assert s.is_local is True
