"""Unit tests for GetPublicBadgeDesignsUseCase."""

import base64
import json
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
    mock_repo.query_public_catalog.return_value = ([sample_design], None)

    use_case = GetPublicBadgeDesignsUseCase(
        badge_design_repository=mock_repo,
        media_url_resolver=mock_resolver,
    )
    result = use_case.execute(year='2026')

    mock_repo.query_public_catalog.assert_called_once_with(
        year='2026',
        year_gt=None,
        year_lt=None,
        limit=10,
        last_evaluated_key=None,
    )
    mock_resolver.resolve_url.assert_called_once_with('designs/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d/badge_artwork.webp')
    assert len(result.data) == 1
    assert result.last_evaluated_key is None
    item = result.data[0]
    assert item.design_id == '1f88efbc-166e-4775-b985-e3d517c2a71f'
    assert item.name == 'April Participant Badge'
    assert item.role == 'participant'
    assert item.meetup_name == 'DurianPy April Meetup'
    assert item.meetup_date == '2026-04-24T14:50:00Z'
    assert item.venue == 'DevHub Davao'
    assert item.design_url == 'https://cdn.example.com/designs/design-1/badge.webp'


def test_use_case_encodes_and_decodes_catalog_cursor() -> None:
    """Verify DynamoDB continuation keys are exchanged as opaque URL-safe tokens."""
    mock_repo = MagicMock(spec=BadgeDesignRepositoryPort)
    mock_resolver = MagicMock(spec=MediaUrlResolverPort)
    mock_repo.query_public_catalog.return_value = ([], {'pk': {'S': 'MEETUP#m-1'}, 'sk': {'S': 'BADGEDESIGN#d-1'}})

    use_case = GetPublicBadgeDesignsUseCase(mock_repo, mock_resolver)
    first_page = use_case.execute(year='2026')

    assert first_page.last_evaluated_key is not None
    decoded = base64.urlsafe_b64decode(first_page.last_evaluated_key + '===').decode()
    assert json.loads(decoded) == {'pk': {'S': 'MEETUP#m-1'}, 'sk': {'S': 'BADGEDESIGN#d-1'}}

    mock_repo.query_public_catalog.return_value = ([], None)
    use_case.execute(year='2026', last_evaluated_key=first_page.last_evaluated_key)
    assert mock_repo.query_public_catalog.call_args.kwargs['last_evaluated_key'] == json.loads(decoded)
