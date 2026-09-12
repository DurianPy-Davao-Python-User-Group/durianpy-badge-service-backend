"""Unit tests for PynamoDB BaseTableEntity and BadgeDesign model."""

from datetime import datetime, timezone

from src.core.settings import settings
from src.infrastructure.db.models.badge_design import BadgeDesign
from src.infrastructure.db.models.base_table import BaseTableEntity


def test_base_table_entity_table_name() -> None:
    """Verify BaseTableEntity Meta table_name matches settings.DYNAMODB_MAIN_TABLE_NAME."""
    assert BaseTableEntity.Meta.table_name == settings.DYNAMODB_MAIN_TABLE_NAME
    assert BaseTableEntity.Meta.region == settings.REGION


def test_base_table_entity_audit_attributes() -> None:
    """Verify BaseTableEntity inherits audit attributes with correct types."""
    instance = BadgeDesign(
        pk='MEETUP#m-100',
        sk='BADGEDESIGN#d-001',
        design_id='d-001',
        meetup_id='m-100',
        name='PyCon Badge',
        storage_path='s3://durianpy-badges/design-1.png',
        role='speaker',
        durianpy_created_by='admin_user',
    )

    assert instance.pk == 'MEETUP#m-100'
    assert instance.sk == 'BADGEDESIGN#d-001'
    assert instance.durianpy_created_by == 'admin_user'
    assert isinstance(instance.durianpy_created_at, datetime)
    assert isinstance(instance.durianpy_updated_at, datetime)
    assert instance.durianpy_created_at.tzinfo == timezone.utc
    assert instance.durianpy_updated_at.tzinfo == timezone.utc
    assert issubclass(BadgeDesign, BaseTableEntity)
    assert instance.durianpy_updated_by is None


def test_badge_design_gsi1_attributes() -> None:
    """Verify BadgeDesign supports GSI1 index key schema and JSON speakers attribute."""
    speakers_list = [{'name': 'Jane Doe', 'topic': 'Python & AWS'}]
    instance = BadgeDesign(
        pk='MEETUP#m-200',
        sk='BADGEDESIGN#d-002',
        gsi1pk='YEAR#2026',
        gsi1sk='MEETUPDATE#2026-08-23T20:00:00Z',
        design_id='d-002',
        meetup_id='m-200',
        name='Davao Tech Meetup Badge',
        storage_path='s3://durianpy-badges/design-2.png',
        role='attendee',
        speakers=speakers_list,
        durianpy_created_by='system',
    )

    assert instance.pk == 'MEETUP#m-200'
    assert instance.sk == 'BADGEDESIGN#d-002'

    assert instance.gsi1pk == 'YEAR#2026'
    assert instance.gsi1sk == 'MEETUPDATE#2026-08-23T20:00:00Z'
    assert instance.design_id == 'd-002'
    assert instance.meetup_id == 'm-200'
    assert instance.name == 'Davao Tech Meetup Badge'
    assert instance.storage_path == 's3://durianpy-badges/design-2.png'
    assert instance.role == 'attendee'
    assert instance.speakers == speakers_list
    assert hasattr(BadgeDesign, 'query_by_year_index')


def test_badge_issuance_attributes() -> None:
    """Verify BadgeIssuance attributes and GSI index support."""
    from src.infrastructure.db.models.badge_issuance import BadgeIssuance

    prev_assignments = [{'role': 'attendee', 'assigned_at': '2026-01-01'}]
    instance = BadgeIssuance(
        pk='BADGEISSUANCE#user@example.com',
        sk='ISSUEDATE#2026-08-23#ISSUANCEID#i-001',
        gsi1pk='MEETUPID#m-100',
        gsi1sk='BADGEISSUANCE#user@example.com',
        gsi2pk='ISSUANCEID#i-001',
        gsi2sk='STATUS#ISSUED',
        issuance_id='i-001',
        design_id='d-001',
        meetup_id='m-100',
        role='speaker',
        updated_by='admin',
        previous_assignments=prev_assignments,
        durianpy_created_by='system',
    )

    assert instance.pk == 'BADGEISSUANCE#user@example.com'
    assert instance.sk == 'ISSUEDATE#2026-08-23#ISSUANCEID#i-001'
    assert instance.gsi1pk == 'MEETUPID#m-100'
    assert instance.gsi1sk == 'BADGEISSUANCE#user@example.com'
    assert instance.gsi2pk == 'ISSUANCEID#i-001'
    assert instance.gsi2sk == 'STATUS#ISSUED'
    assert instance.issuance_id == 'i-001'
    assert instance.design_id == 'd-001'
    assert instance.meetup_id == 'm-100'
    assert instance.role == 'speaker'
    assert instance.updated_by == 'admin'
    assert instance.previous_assignments == prev_assignments
    assert hasattr(BadgeIssuance, 'query_by_meetup_index')
    assert hasattr(BadgeIssuance, 'query_by_email_issuance_index')
