"""Abstract use case port contract for creating a badge design."""

from abc import abstractmethod

from src.application.dtos.badge_design_dto import BadgeDesignOutputDTO, CreateBadgeDesignInputDTO
from src.application.ports.use_case_port import UseCasePort


class CreateBadgeDesignUseCasePort(UseCasePort):
    """Abstract boundary contract for the create badge design use case."""

    @abstractmethod
    def execute(self, input_dto: CreateBadgeDesignInputDTO) -> BadgeDesignOutputDTO:
        """Persist a new badge design blueprint and return its output representation.

        :param input_dto: Validated input data for the new badge design.
        :type input_dto: CreateBadgeDesignInputDTO
        :returns: Output DTO representing the persisted badge design.
        :rtype: BadgeDesignOutputDTO
        :raises BadgeDesignVariantValidationError: If role-specific domain invariants are violated.
        :raises BadgeDesignCreationError: If persisting the badge design to the repository fails.
        """
        pass
