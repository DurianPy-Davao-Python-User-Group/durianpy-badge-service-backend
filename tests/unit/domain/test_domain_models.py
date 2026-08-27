"""Unit tests for domain models including MeetupDetailDomainModel."""

from src.domain.models.badge_design import BadgeDesignDomainModel
from src.domain.models.badge_issuance import BadgeIssuanceDomainModel
from src.domain.models.meetup_detail import MeetupDetailDomainModel


def test_meetup_detail_domain_model() -> None:
    """Verify MeetupDetailDomainModel initialization and field access."""
    meetup = MeetupDetailDomainModel(
        meetup_id='m-100',
        name='PyCon Davao 2026',
        date='2026-08-23',
        venue='Davao Convention Center',
    )
    assert meetup.meetup_id == 'm-100'
    assert meetup.name == 'PyCon Davao 2026'
    assert meetup.date == '2026-08-23'
    assert meetup.venue == 'Davao Convention Center'


def test_badge_design_domain_model_with_meetup_detail() -> None:
    """Verify BadgeDesignDomainModel composes MeetupDetailDomainModel."""
    meetup = MeetupDetailDomainModel(meetup_id='m-100', name='PyCon Davao 2026')
    design = BadgeDesignDomainModel(
        design_id='d-001',
        name='Speaker Badge',
        storage_path='s3://durianpy-badges/design-1.png',
        role='speaker',
        speakers=[{'name': 'Jane Doe'}],
        meetup_detail=meetup,
    )
    assert design.design_id == 'd-001'
    assert design.meetup_detail.meetup_id == 'm-100'
    assert design.meetup_detail.name == 'PyCon Davao 2026'
    assert design.speakers == [{'name': 'Jane Doe'}]


def test_badge_issuance_domain_model_with_meetup_detail() -> None:
    """Verify BadgeIssuanceDomainModel composes optional MeetupDetailDomainModel."""
    meetup = MeetupDetailDomainModel(meetup_id='m-100', venue='Online')
    issuance = BadgeIssuanceDomainModel(
        issuance_id='i-001',
        email='user@example.com',
        design_id='d-001',
        role='attendee',
        meetup_detail=meetup,
    )
    assert issuance.issuance_id == 'i-001'
    assert issuance.email == 'user@example.com'
    assert issuance.meetup_detail is not None
    assert issuance.meetup_detail.venue == 'Online'
