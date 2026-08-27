"""Mock DynamoDB table initialization and seeding using Moto."""

import os
from typing import Optional

from moto import mock_aws

from src.core.logging import logger
from src.core.settings import settings
from src.domain.models.badge_design import BadgeDesignDomainModel
from src.domain.models.meetup_detail import MeetupDetailDomainModel
from src.infrastructure.db.models.badge_design import BadgeDesign
from src.infrastructure.db.pynamo_repositories.pynamo_badge_design_repository import (
    PynamoBadgeDesignRepository,
)

__mock_instance: Optional[mock_aws] = None
__is_initialized: bool = False


def seed_sample_badge_designs(repository: PynamoBadgeDesignRepository) -> None:
    """Seed initial sample badge designs for public catalog discovery."""
    sample_design = BadgeDesignDomainModel(
        design_id='1f88efbc-166e-4775-b985-e3d517c2a71f',
        name='April Participant Badge',
        storage_path='designs/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d/badge_artwork.webp',
        role='participant',
        meetup_detail=MeetupDetailDomainModel(
            meetup_id='m-april-2026',
            name='DurianPy April Meetup',
            date='2026-04-24T14:50:00Z',
            venue='DevHub Davao',
        ),
    )

    repository.create_design(
        design=sample_design,
        year='2026',
        iso_date='2026-04-24T14:50:00Z',
        created_by='system_seeder',
    )
    logger.info('Sample badge designs seeded into mock DynamoDB table.')


def ensure_mock_database() -> None:
    """Ensure moto mock DynamoDB table is initialized and seeded with mock catalog data."""
    global __mock_instance, __is_initialized
    if __is_initialized:
        return

    os.environ.setdefault('AWS_DEFAULT_REGION', settings.REGION)
    os.environ.setdefault('AWS_ACCESS_KEY_ID', 'mock_key')
    os.environ.setdefault('AWS_SECRET_ACCESS_KEY', 'mock_secret')
    os.environ.setdefault('AWS_SECURITY_TOKEN', 'mock_token')
    os.environ.setdefault('AWS_SESSION_TOKEN', 'mock_token')

    __mock_instance = mock_aws()
    __mock_instance.start()

    if not BadgeDesign.exists():
        BadgeDesign.create_table(
            read_capacity_units=1,
            write_capacity_units=1,
            wait=True,
        )
        repo = PynamoBadgeDesignRepository()
        seed_sample_badge_designs(repo)

    __is_initialized = True
