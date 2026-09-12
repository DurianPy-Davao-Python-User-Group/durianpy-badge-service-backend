"""Unit tests for badge issuance DTOs."""

from src.application.dtos.badge_design_dto import MeetupDetailDTO
from src.application.dtos.badge_issuance_dto import (
    BadgeIssuanceOutputDTO,
    UserPortfolioQueryDTO,
)


def test_user_portfolio_query_dto_instantiation() -> None:
    """
    Verify UserPortfolioQueryDTO creation with required and optional fields.

    :returns: None
    """
    dto = UserPortfolioQueryDTO(email='user@durianpy.org')
    assert dto.email == 'user@durianpy.org'
    assert dto.year is None

    dto_with_year = UserPortfolioQueryDTO(email='user@durianpy.org', year='2026')
    assert dto_with_year.year == '2026'


def test_badge_issuance_output_dto_instantiation() -> None:
    """
    Verify BadgeIssuanceOutputDTO serialization and field assignments.

    :returns: None
    """
    meetup = MeetupDetailDTO(
        meetup_id='meetup-1',
        name='DurianPy 2026',
        date='2026-04-20T10:00:00Z',
        venue='DevHub Davao',
    )
    dto = BadgeIssuanceOutputDTO(
        issuance_id='iss-123',
        email='user@durianpy.org',
        design_id='des-456',
        role='speaker',
        updated_by='admin',
        previous_assignments=[{'role': 'attendee'}],
        meetup_detail=meetup,
    )
    assert dto.issuance_id == 'iss-123'
    assert dto.email == 'user@durianpy.org'
    assert dto.design_id == 'des-456'
    assert dto.role == 'speaker'
    assert dto.updated_by == 'admin'
    assert dto.previous_assignments == [{'role': 'attendee'}]
    assert dto.meetup_detail is not None
    assert dto.meetup_detail.name == 'DurianPy 2026'


def test_badge_issuance_output_dto_defaults() -> None:
    """
    Verify BadgeIssuanceOutputDTO default optional values.

    :returns: None
    """
    dto = BadgeIssuanceOutputDTO(
        issuance_id='iss-123',
        email='user@durianpy.org',
        design_id='des-456',
    )
    assert dto.role is None
    assert dto.updated_by is None
    assert dto.previous_assignments is None
    assert dto.meetup_detail is None
