"""Moto mock unit tests for PynamoBadgeDesignRepository."""

from unittest.mock import patch

import pytest
from pynamodb.exceptions import TableDoesNotExist

from src.domain.exceptions.badge_design_exceptions import (
    BadgeDesignCreationError,
    BadgeDesignQueryError,
)
from src.domain.models.badge_design import BadgeDesignDomainModel
from src.domain.models.meetup_detail import MeetupDetailDomainModel
from src.infrastructure.db.models.badge_design import BadgeDesign
from src.infrastructure.db.pynamo_repositories.pynamo_badge_design_repository import (
    PynamoBadgeDesignRepository,
)


def test_moto_create_design(
    mock_dynamodb_table: None,
    badge_design_repository: PynamoBadgeDesignRepository,
) -> None:
    """Verify persisting a badge design with moto using TransactWrite."""
    meetup = MeetupDetailDomainModel(
        meetup_id='meetup-101',
        name='PyCon PH 2026',
        date='2026-08-23',
        venue='SMX Davao',
    )
    design = BadgeDesignDomainModel(
        design_id='design-001',
        name='Speaker Badge',
        storage_path='s3://badges/design-001.png',
        role='speaker',
        speakers=[{'name': 'Guido', 'topic': 'Python Core'}],
        meetup_detail=meetup,
    )

    created = badge_design_repository.create_design(
        design=design,
        year='2026',
        iso_date='2026-08-23T09:00:00Z',
        created_by='admin_user',
    )

    assert isinstance(created, BadgeDesignDomainModel)
    assert created.design_id == 'design-001'
    assert created.name == 'Speaker Badge'
    assert created.role == 'speaker'
    assert created.meetup_detail.meetup_id == 'meetup-101'
    assert created.meetup_detail.name == 'PyCon PH 2026'

    # Verify directly from DynamoDB
    saved_record = BadgeDesign.get('MEETUP#meetup-101', 'BADGEDESIGN#design-001')
    assert saved_record.name == 'Speaker Badge'
    assert saved_record.gsi1pk == 'YEAR#2026'
    assert saved_record.gsi1sk == 'MEETUPDATE#2026-08-23T09:00:00Z'
    assert saved_record.durianpy_created_by == 'admin_user'


def test_moto_create_design_raises_domain_exception_on_db_error(
    badge_design_repository: PynamoBadgeDesignRepository,
) -> None:
    """Verify create_design translates DB errors into BadgeDesignCreationError."""
    meetup = MeetupDetailDomainModel(meetup_id='m-1')
    design = BadgeDesignDomainModel(
        design_id='d-1',
        name='Test',
        storage_path='path',
        role='participant',
        meetup_detail=meetup,
    )

    with patch('src.infrastructure.db.pynamo_repositories.pynamo_badge_design_repository.TransactWrite') as mock_tw:
        mock_tw.side_effect = TableDoesNotExist('Table missing')
        with pytest.raises(BadgeDesignCreationError) as exc_info:
            badge_design_repository.create_design(
                design=design,
                year='2026',
                iso_date='2026-01-01',
                created_by='user',
            )

        assert 'Failed to persist badge design in DynamoDB' in str(exc_info.value)


def test_moto_to_domain_mapping(
    badge_design_repository: PynamoBadgeDesignRepository,
) -> None:
    """Verify __to_domain private method maps BadgeDesign to BadgeDesignDomainModel."""
    record = BadgeDesign(
        pk='MEETUP#meetup-101',
        sk='BADGEDESIGN#design-001',
        gsi1pk='YEAR#2026',
        gsi1sk='MEETUPDATE#2026-08-23T09:00:00Z',
        design_id='design-001',
        meetup_id='meetup-101',
        name='Speaker Badge',
        storage_path='s3://badges/design-001.png',
        role='speaker',
        speakers=[{'name': 'Guido'}],
        meetup_name='PyCon PH 2026',
        meetup_date='2026-08-23',
        venue='SMX Davao',
        durianpy_created_by='tester',
    )
    to_domain_fn = getattr(badge_design_repository, '_PynamoBadgeDesignRepository__to_domain')
    domain: BadgeDesignDomainModel = to_domain_fn(record)
    assert isinstance(domain, BadgeDesignDomainModel)
    assert domain.design_id == 'design-001'
    assert domain.meetup_detail.meetup_id == 'meetup-101'
    assert domain.speakers == [{'name': 'Guido'}]


def test_moto_query_public_catalog_all_and_filters(
    mock_dynamodb_table: None,
    badge_design_repository: PynamoBadgeDesignRepository,
) -> None:
    """Verify query_public_catalog with TransactGet against moto DynamoDB."""
    seed_data = [
        ('d-1', 'm-1', '2026', '2026-03-15T10:00:00Z', 'Q1 Meetup'),
        ('d-2', 'm-2', '2026', '2026-06-20T14:00:00Z', 'Q2 Meetup'),
        ('d-3', 'm-3', '2026', '2026-09-10T16:00:00Z', 'Q3 Meetup'),
        ('d-4', 'm-4', '2025', '2025-11-05T09:00:00Z', '2025 Year End'),
    ]

    for d_id, m_id, year, iso_date, name in seed_data:
        badge_design_repository.create_design(
            design=BadgeDesignDomainModel(
                design_id=d_id,
                name=name,
                storage_path=f's3://badges/{d_id}.png',
                role='attendee',
                meetup_detail=MeetupDetailDomainModel(meetup_id=m_id, name=name),
            ),
            year=year,
            iso_date=iso_date,
            created_by='seeder',
        )

    # 1. Query entire 2026 catalog (should return 3 items)
    results_2026 = badge_design_repository.query_public_catalog(year='2026')
    assert len(results_2026) == 3
    assert [r.design_id for r in results_2026] == ['d-1', 'd-2', 'd-3']

    # 2. Query with year_gt
    results_gt = badge_design_repository.query_public_catalog(
        year='2026',
        year_gt='2026-04-01T00:00:00Z',
    )
    assert len(results_gt) == 2
    assert [r.design_id for r in results_gt] == ['d-2', 'd-3']

    # 3. Query with year_lt
    results_lt = badge_design_repository.query_public_catalog(
        year='2026',
        year_lt='2026-07-01T00:00:00Z',
    )
    assert len(results_lt) == 2
    assert [r.design_id for r in results_lt] == ['d-1', 'd-2']

    # 4. Query with between (year_gt and year_lt)
    results_between = badge_design_repository.query_public_catalog(
        year='2026',
        year_gt='2026-04-01T00:00:00Z',
        year_lt='2026-08-01T00:00:00Z',
    )
    assert len(results_between) == 1
    assert results_between[0].design_id == 'd-2'

    # 5. Query 2025 catalog
    results_2025 = badge_design_repository.query_public_catalog(year='2025')
    assert len(results_2025) == 1
    assert results_2025[0].design_id == 'd-4'

    # 6. Query non-existent year
    results_empty = badge_design_repository.query_public_catalog(year='2024')
    assert results_empty == []


def test_moto_query_public_catalog_raises_domain_exception_on_db_error(
    badge_design_repository: PynamoBadgeDesignRepository,
) -> None:
    """Verify query_public_catalog translates DB errors into BadgeDesignQueryError."""
    with patch.object(BadgeDesign.query_by_year_index, 'query') as mock_query:
        mock_query.side_effect = TableDoesNotExist('Table missing')
        with pytest.raises(BadgeDesignQueryError) as exc_info:
            badge_design_repository.query_public_catalog(year='2026')

        assert 'Failed to query public catalog from DynamoDB' in str(exc_info.value)
