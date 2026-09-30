"""Abstract use case port contract for discovering public badge designs."""

from abc import abstractmethod
from typing import Optional

from src.application.dtos.badge_design_dto import PaginatedPublicCatalogOutputDTO
from src.application.ports.use_case_port import UseCasePort


class GetPublicBadgeDesignsUseCasePort(UseCasePort):
    """Abstract boundary contract for public badge designs discovery use case."""

    @abstractmethod
    def execute(
        self,
        year: Optional[str] = None,
        year_gt: Optional[str] = None,
        year_lt: Optional[str] = None,
        limit: int = 10,
        last_evaluated_key: Optional[str] = None,
    ) -> PaginatedPublicCatalogOutputDTO:
        """
        Retrieve public badge design catalog items for a given year.

        :param year: Optional target catalog year.
        :type year: Optional[str]
        :returns: A page of designs with an optional opaque continuation token.
        :rtype: PaginatedPublicCatalogOutputDTO
        """
        pass
