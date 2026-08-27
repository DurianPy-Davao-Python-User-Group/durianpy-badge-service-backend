"""Abstract use case port contract for discovering public badge designs."""

from abc import abstractmethod
from typing import Optional

from src.application.dtos.badge_design_dto import PublicBadgeDesignOutputDTO
from src.application.ports.use_case_port import UseCasePort


class GetPublicBadgeDesignsUseCasePort(UseCasePort):
    """Abstract boundary contract for public badge designs discovery use case."""

    @abstractmethod
    def execute(
        self,
        year: Optional[str] = None,
    ) -> list[PublicBadgeDesignOutputDTO]:
        """
        Retrieve public badge design catalog items for a given year.

        :param year: Optional target catalog year.
        :type year: Optional[str]
        :returns: List of PublicBadgeDesignOutputDTO items with resolved design URLs.
        :rtype: list[PublicBadgeDesignOutputDTO]
        """
        pass
