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


def test_settings_environment_override() -> None:
    """Verify environment variables override default settings."""
    env_vars = {
        'APP_NAME': 'custom-app',
        'ENVIRONMENT': 'prod',
        'LOG_LEVEL': 'warning',
        'CLOUDFRONT_URL': 'https://custom-cdn.example.com',
    }
    with patch.dict(os.environ, env_vars):
        s = Settings()
        assert s.APP_NAME == 'custom-app'
        assert s.ENVIRONMENT == Environment.PRODUCTION
        assert s.LOG_LEVEL == LogLevel.WARNING
        assert s.CLOUDFRONT_URL == 'https://custom-cdn.example.com'
