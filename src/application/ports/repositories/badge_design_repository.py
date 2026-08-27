"""Abstract repository port contract for badge design persistence."""

from abc import ABC, abstractmethod
from typing import Optional

from src.domain.models.badge_design import BadgeDesignDomainModel


class BadgeDesignRepositoryPort(ABC):
    """Abstract repository boundary contract for badge design entity persistence."""

    @abstractmethod
    def create_design(
        self,
        design: BadgeDesignDomainModel,
        year: str,
        iso_date: str,
        created_by: str,
    ) -> BadgeDesignDomainModel:
        """
        Persist a new badge design blueprint item.

        :param design: Badge design domain entity.
        :type design: BadgeDesignDomainModel
        :param year: Target catalog year.
        :type year: str
        :param iso_date: Target ISO date for sorting.
        :type iso_date: str
        :param created_by: Creator identifier for audit attribution.
        :type created_by: str
        :returns: Persisted BadgeDesignDomainModel instance.
        :rtype: BadgeDesignDomainModel
        """
        pass

    @abstractmethod
    def query_public_catalog(
        self,
        year: str,
        year_gt: Optional[str] = None,
        year_lt: Optional[str] = None,
    ) -> list[BadgeDesignDomainModel]:
        """Query public catalog badge designs for a given year with date filters.

        :param year: Target catalog year (YYYY).
        :type year: str
        :param year_gt: Optional lower bound ISO date filter.
        :type year_gt: Optional[str]
        :param year_lt: Optional upper bound ISO date filter.
        :type year_lt: Optional[str]
        :returns: List of matching BadgeDesignDomainModel instances.
        :rtype: list[BadgeDesignDomainModel]
        """
        pass
