"""Core settings configuration module for the application."""

from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Enumeration of application deployment environments."""

    DEVELOPMENT = 'dev'
    PRODUCTION = 'prod'


class LogLevel(str, Enum):
    """Enumeration of supported logging levels."""

    DEBUG = 'debug'
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'


class Settings(BaseSettings):
    """Application setting values loaded from environment variables or .env file."""

    APP_NAME: str = 'DurianPy Badge System'
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    LOG_LEVEL: LogLevel = LogLevel.DEBUG

    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8', extra='ignore'
    )
