"""Unit tests for public catalog discovery API route controller."""

from fastapi.testclient import TestClient
from moto import mock_aws

from src.core.settings import settings
from src.domain.models.badge_design import BadgeDesignDomainModel
from src.domain.models.meetup_detail import MeetupDetailDomainModel
from src.infrastructure.db.models.badge_design import BadgeDesign
from src.infrastructure.db.pynamo_repositories.pynamo_badge_design_repository import (
    PynamoBadgeDesignRepository,
)
from src.presentation.api.main import app


def _seed_sample_badge_designs(repository: PynamoBadgeDesignRepository) -> None:
    """
    Seed sample badge designs into the test DynamoDB table for catalog testing.

    :param repository: Badge design repository instance.
    :type repository: PynamoBadgeDesignRepository
    """
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


def test_get_public_badge_designs_endpoint_returns_catalog() -> None:
    """Verify GET /api/public/designs returns 200 OK with expected JSON structure and camelCase keys."""
    with mock_aws():
        if not BadgeDesign.exists():
            BadgeDesign.create_table(
                read_capacity_units=1,
                write_capacity_units=1,
                wait=True,
            )
            _seed_sample_badge_designs(PynamoBadgeDesignRepository())

        client = TestClient(app)
        response = client.get('/api/public/designs')

        assert response.status_code == 200
        data = response.json()
        assert 'data' in data
        assert isinstance(data['data'], list)
        assert len(data['data']) >= 1

        first_item = data['data'][0]
        assert 'designId' in first_item
        assert 'meetupName' in first_item
        assert 'meetupDate' in first_item
        assert 'venue' in first_item
        assert 'name' in first_item
        assert 'designUrl' in first_item
        assert 'role' in first_item

        assert first_item['designId'] == '1f88efbc-166e-4775-b985-e3d517c2a71f'
        assert first_item['meetupName'] == 'DurianPy April Meetup'
        assert first_item['meetupDate'] == '2026-04-24T14:50:00Z'
        assert first_item['venue'] == 'DevHub Davao'
        assert first_item['name'] == 'April Participant Badge'
        assert first_item['role'] == 'participant'
        assert first_item['designUrl'] == (
            f'{settings.CLOUDFRONT_URL.rstrip("/")}/designs/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d/badge_artwork.webp'
        )


def test_get_public_badge_designs_endpoint_with_year_query() -> None:
    """Verify GET /api/public/designs?year=2026 filters catalog by year parameter."""
    with mock_aws():
        if not BadgeDesign.exists():
            BadgeDesign.create_table(
                read_capacity_units=1,
                write_capacity_units=1,
                wait=True,
            )
            _seed_sample_badge_designs(PynamoBadgeDesignRepository())

        client = TestClient(app)
        response = client.get('/api/public/designs?year=2026')

        assert response.status_code == 200
        data = response.json()
        assert 'data' in data
        assert isinstance(data['data'], list)
        assert len(data['data']) >= 1


def test_get_public_badge_designs_endpoint_with_invalid_year() -> None:
    """Verify GET /api/public/designs?year=invalid returns 422 Unprocessable Entity."""
    client = TestClient(app)
    response = client.get('/api/public/designs?year=invalid_year')
    assert response.status_code == 422
    assert response.json()['error']['code'] == 'REQUEST_VALIDATION_ERROR'
