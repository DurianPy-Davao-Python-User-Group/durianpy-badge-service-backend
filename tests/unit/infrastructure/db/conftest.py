"""Reusable pytest fixtures for database infrastructure tests."""

import os
from typing import Generator

import pytest
from moto import mock_aws

from src.infrastructure.db.models.badge_design import BadgeDesign
from src.infrastructure.db.pynamo_repositories.pynamo_badge_design_repository import (
    PynamoBadgeDesignRepository,
)


@pytest.fixture(autouse=True)
def aws_credentials() -> None:
    """Set mock AWS credentials for moto."""
    os.environ['AWS_DEFAULT_REGION'] = 'ap-southeast-1'
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'


@pytest.fixture
def mock_dynamodb_table() -> Generator[None, None, None]:
    """Provision a mocked DynamoDB table for BadgeDesign using moto."""
    with mock_aws():
        if not BadgeDesign.exists():
            BadgeDesign.create_table(
                read_capacity_units=1,
                write_capacity_units=1,
                wait=True,
            )
        yield
        if BadgeDesign.exists():
            BadgeDesign.delete_table()


@pytest.fixture
def badge_design_repository() -> PynamoBadgeDesignRepository:
    """Provide a PynamoBadgeDesignRepository fixture instance."""
    return PynamoBadgeDesignRepository()
