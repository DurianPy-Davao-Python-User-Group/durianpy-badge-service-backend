"""Use case for discovering and retrieving public badge designs catalog."""

from datetime import datetime, timezone
from typing import Optional

from src.application.dtos.badge_design_dto import PublicBadgeDesignOutputDTO
from src.application.ports.repositories.badge_design_repository import (
    BadgeDesignRepositoryPort,
)
from src.application.ports.storage.media_url_resolver_port import (
    MediaUrlResolverPort,
)
from src.application.ports.use_cases.get_public_badge_designs_use_case_port import (
    GetPublicBadgeDesignsUseCasePort,
)
from src.core.logging import log_execution


class GetPublicBadgeDesignsUseCase(GetPublicBadgeDesignsUseCasePort):
    """Use case interactor for public badge design catalog discovery."""

    def __init__(
        self,
        badge_design_repository: BadgeDesignRepositoryPort,
        media_url_resolver: MediaUrlResolverPort,
    ) -> None:
        """
        Initialize the use case with required repository and media resolver dependencies.

        :param badge_design_repository: Persistence repository port for badge designs.
        :type badge_design_repository: BadgeDesignRepositoryPort
        :param media_url_resolver: Port for resolving asset storage paths to public URLs.
        :type media_url_resolver: MediaUrlResolverPort
        """
        self.__repository = badge_design_repository
        self.__media_url_resolver = media_url_resolver

    @log_execution
    def execute(
        self,
        year: Optional[str] = None,
        # TODO: Query params gt and lt year
        # year_gt: Optional[str] = None,
        # year_lt: Optional[str] = None,
        # TODO: Pagination
        # page: int = 1,
        # limit: int = 20,
    ) -> list[PublicBadgeDesignOutputDTO]:
        """
        Retrieve public badge design catalog items for a given year.

        :param year: Optional target catalog year. Defaults to current UTC year.
        :type year: Optional[str]
        :returns: List of PublicBadgeDesignOutputDTO items with resolved design URLs.
        :rtype: list[PublicBadgeDesignOutputDTO]
        """
        target_year = year or datetime.now(timezone.utc).strftime('%Y')
        designs = self.__repository.query_public_catalog(year=target_year)

        catalog_items: list[PublicBadgeDesignOutputDTO] = []
        for design in designs:
            design_url = self.__media_url_resolver.resolve_url(design.storage_path)

            catalog_items.append(
                PublicBadgeDesignOutputDTO(
                    design_id=design.design_id,
                    meetup_name=design.meetup_detail.name,
                    meetup_date=design.meetup_detail.date,
                    venue=design.meetup_detail.venue,
                    name=design.name,
                    design_url=design_url,
                    role=design.role,
                )
            )

        return catalog_items
