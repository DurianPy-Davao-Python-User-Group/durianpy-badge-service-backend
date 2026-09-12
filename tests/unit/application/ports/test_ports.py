"""Unit tests verifying abstract application port contracts."""

from typing import Any, Optional

import pytest

from src.application.ports.repositories.badge_design_repository import (
    BadgeDesignRepositoryPort,
)
from src.application.ports.repositories.badge_issuance_repository import (
    BadgeIssuanceRepositoryPort,
)
from src.application.ports.storage.media_url_resolver_port import (
    MediaUrlResolverPort,
)
from src.application.ports.use_case_port import UseCasePort
from src.application.ports.use_cases.get_public_badge_designs_use_case_port import (
    GetPublicBadgeDesignsUseCasePort,
)
from src.domain.models.badge_design import BadgeDesignDomainModel
from src.domain.models.badge_issuance import BadgeIssuanceDomainModel
from src.domain.models.meetup_detail import MeetupDetailDomainModel


def test_use_case_port_contract() -> None:
    """
    Verify UseCasePort cannot be instantiated directly and permits implementation.

    :returns: None
    """
    with pytest.raises(TypeError):
        UseCasePort()  # type: ignore[abstract]

    class ConcreteUseCase(UseCasePort):
        def execute(self, *args: Any, **kwargs: Any) -> Any:
            super().execute(*args, **kwargs)
            return 'executed'

    instance = ConcreteUseCase()
    assert instance.execute() == 'executed'


def test_get_public_badge_designs_use_case_port_contract() -> None:
    """
    Verify GetPublicBadgeDesignsUseCasePort cannot be instantiated directly.

    :returns: None
    """
    with pytest.raises(TypeError):
        GetPublicBadgeDesignsUseCasePort()  # type: ignore[abstract]

    class ConcreteCatalogUseCase(GetPublicBadgeDesignsUseCasePort):
        def execute(
            self,
            year: Optional[str] = None,
        ) -> Any:
            super().execute(year=year)
            return []

    instance = ConcreteCatalogUseCase()
    assert instance.execute(year='2026') == []


def test_badge_issuance_repository_port_contract() -> None:
    """
    Verify BadgeIssuanceRepositoryPort cannot be instantiated directly.

    :returns: None
    """
    with pytest.raises(TypeError):
        BadgeIssuanceRepositoryPort()  # type: ignore[abstract]

    class ConcreteIssuanceRepo(BadgeIssuanceRepositoryPort):
        def query_user_portfolio(
            self,
            email: str,
            year: Optional[str] = None,
        ) -> list[BadgeIssuanceDomainModel]:
            super().query_user_portfolio(email, year)
            return []

    instance = ConcreteIssuanceRepo()
    assert instance.query_user_portfolio('test@durianpy.org', '2026') == []


def test_badge_design_repository_port_contract() -> None:
    """
    Verify BadgeDesignRepositoryPort cannot be instantiated directly.

    :returns: None
    """
    with pytest.raises(TypeError):
        BadgeDesignRepositoryPort()  # type: ignore[abstract]

    class ConcreteDesignRepo(BadgeDesignRepositoryPort):
        def create_design(
            self,
            design: BadgeDesignDomainModel,
            year: str,
            iso_date: str,
            created_by: str,
        ) -> BadgeDesignDomainModel:
            super().create_design(design, year, iso_date, created_by)
            return design

        def query_public_catalog(
            self,
            year: str,
            year_gt: Optional[str] = None,
            year_lt: Optional[str] = None,
        ) -> list[BadgeDesignDomainModel]:
            super().query_public_catalog(year, year_gt, year_lt)
            return []

    dummy_design = BadgeDesignDomainModel(
        design_id='d-1',
        name='Test Badge',
        storage_path='s3://badges/1/art.webp',
        role='attendee',
        meetup_detail=MeetupDetailDomainModel(meetup_id='m-1'),
    )
    repo = ConcreteDesignRepo()
    assert repo.create_design(dummy_design, '2026', '2026-01-01', 'admin') == dummy_design
    assert repo.query_public_catalog('2026') == []


def test_media_url_resolver_port_contract() -> None:
    """
    Verify MediaUrlResolverPort cannot be instantiated directly.

    :returns: None
    """
    with pytest.raises(TypeError):
        MediaUrlResolverPort()  # type: ignore[abstract]

    class ConcreteResolver(MediaUrlResolverPort):
        def resolve_url(self, relative_storage_path: str) -> str:
            super().resolve_url(relative_storage_path)
            return f'https://cdn.example.com/{relative_storage_path}'

    resolver = ConcreteResolver()
    assert resolver.resolve_url('path/to/img.webp') == 'https://cdn.example.com/path/to/img.webp'
