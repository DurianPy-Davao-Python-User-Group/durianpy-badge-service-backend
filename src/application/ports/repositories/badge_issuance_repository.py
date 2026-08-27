"""Abstract repository port contract for badge issuance persistence."""

from abc import ABC, abstractmethod
from typing import Optional

from src.domain.models.badge_issuance import BadgeIssuanceDomainModel


class BadgeIssuanceRepositoryPort(ABC):
    """Abstract repository boundary contract for badge issuance entity persistence."""

    @abstractmethod
    def query_user_portfolio(self, email: str, year: Optional[str] = None) -> list[BadgeIssuanceDomainModel]:
        """
        Query user's acquired badges sorted chronologically by issued date.

        :param email: User email address.
        :type email: str
        :param year: Optional target year to filter issuance date.
        :type year: Optional[str]
        :returns: List of matching BadgeIssuanceDomainModel instances.
        :rtype: list[BadgeIssuanceDomainModel]
        """
        pass
