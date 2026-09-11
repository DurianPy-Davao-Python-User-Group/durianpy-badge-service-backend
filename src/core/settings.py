"""Core settings configuration module for the application."""

import os
from enum import Enum

from pydantic import model_validator
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
    """Application setting values loaded from environment variables and local .env file."""

    # Base Settings
    APP_NAME: str = 'durianpy-badge-system'
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    LOG_LEVEL: LogLevel = LogLevel.DEBUG

    # AWS Settings
    REGION: str = 'ap-southeast-1'
    CLOUDFRONT_URL: str = ''
    DYNAMODB_MAIN_TABLE_NAME: str = ''

    # Swagger Documentation Basic Auth Settings
    ENABLE_SWAGGER_BASIC_AUTH: bool = False
    SWAGGER_BASIC_AUTH_USERNAME: str = ''
    SWAGGER_BASIC_AUTH_PASSWORD: str = ''

    @property
    def is_local(self) -> bool:
        """
        Check if the application is running in a local environment outside AWS Lambda.

        :returns: True if running locally, False if executing inside an AWS Lambda runtime.
        :rtype: bool
        """
        return not bool(os.getenv('AWS_LAMBDA_FUNCTION_NAME'))

    @model_validator(mode='after')
    def __set_default_table_name(self) -> 'Settings':
        """Ensure DYNAMODB_MAIN_TABLE_NAME defaults to {env}-{app}-main if not explicitly configured."""
        if not self.DYNAMODB_MAIN_TABLE_NAME:
            self.DYNAMODB_MAIN_TABLE_NAME = f'{self.ENVIRONMENT.value}-{self.APP_NAME}-main'
        return self

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )

    # Uncomment when pydantic-settings d26fc0c is released to support
    # AWS Systems Manager Parameter Store as a settings source.
    # @classmethod
    # def settings_customise_sources(
    #     cls,
    #     settings_cls: type[BaseSettings],
    #     init_settings: PydanticBaseSettingsSource,
    #     env_settings: PydanticBaseSettingsSource,
    #     dotenv_settings: PydanticBaseSettingsSource,
    #     file_secret_settings: PydanticBaseSettingsSource,
    # ) -> tuple[PydanticBaseSettingsSource, ...]:
    #     aws_systems_manager_settings = AWSSystemsManagerSettingsSource(
    #         settings_cls,
    #         ssm_path='/durianpy-badge-system/backend/',
    #     )
    #     return (
    #         init_settings,
    #         aws_systems_manager_settings,
    #         env_settings,
    #         dotenv_settings,
    #         file_secret_settings,
    #     )


settings = Settings()
