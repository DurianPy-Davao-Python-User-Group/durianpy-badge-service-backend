"""Unit tests for GetPublicBadgeDesignsUseCase."""

from unittest.mock import MagicMock

from src.application.ports.repositories.badge_design_repository import (
    BadgeDesignRepositoryPort,
)
from src.application.ports.storage.media_url_resolver_port import (
    MediaUrlResolverPort,
)
from src.application.ports.use_case_port import UseCasePort
from src.application.ports.use_cases.get_public_badge_designs_use_case_port import (
    GetPublicBadgeDesignsUseCasePort,
)
from src.application.use_cases.get_public_badge_designs_use_case import (
    GetPublicBadgeDesignsUseCase,
)
from src.domain.models.badge_design import BadgeDesignDomainModel
from src.domain.models.meetup_detail import MeetupDetailDomainModel


def test_use_case_implements_port() -> None:
    """Verify GetPublicBadgeDesignsUseCase implements GetPublicBadgeDesignsUseCasePort and UseCasePort."""
    assert issubclass(GetPublicBadgeDesignsUseCase, GetPublicBadgeDesignsUseCasePort)
    assert issubclass(GetPublicBadgeDesignsUseCase, UseCasePort)
    assert hasattr(GetPublicBadgeDesignsUseCase, 'execute')
    assert callable(getattr(GetPublicBadgeDesignsUseCase, 'execute'))


def test_get_public_badge_designs_use_case_execution() -> None:
    """Verify GetPublicBadgeDesignsUseCase retrieves items and uses media URL resolver."""
    mock_repo = MagicMock(spec=BadgeDesignRepositoryPort)
    mock_resolver = MagicMock(spec=MediaUrlResolverPort)

    mock_resolver.resolve_url.return_value = 'https://cdn.example.com/designs/design-1/badge.webp'

    sample_design = BadgeDesignDomainModel(
        design_id='1f88efbc-166e-4775-b985-e3d517c2a71f',
        name='April Participant Badge',
        storage_path='designs/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d/badge_artwork.webp',
        role='participant',
        meetup_detail=MeetupDetailDomainModel(
            meetup_id='m-100',
            name='DurianPy April Meetup',
            date='2026-04-24T14:50:00Z',
            venue='DevHub Davao',
        ),
    )
    mock_repo.query_public_catalog.return_value = [sample_design]

    use_case = GetPublicBadgeDesignsUseCase(
        badge_design_repository=mock_repo,
        media_url_resolver=mock_resolver,
    )
    result = use_case.execute(year='2026')

    mock_repo.query_public_catalog.assert_called_once_with(year='2026')
    mock_resolver.resolve_url.assert_called_once_with('designs/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d/badge_artwork.webp')
    assert len(result) == 1
    item = result[0]
    assert item.design_id == '1f88efbc-166e-4775-b985-e3d517c2a71f'
    assert item.name == 'April Participant Badge'
    assert item.role == 'participant'
    assert item.meetup_name == 'DurianPy April Meetup'
    assert item.meetup_date == '2026-04-24T14:50:00Z'
    assert item.venue == 'DevHub Davao'
    assert item.design_url == 'https://cdn.example.com/designs/design-1/badge.webp'
