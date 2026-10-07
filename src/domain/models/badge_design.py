"""Badge design domain model."""

from enum import StrEnum
from typing import Any, Optional

from pydantic import BaseModel, model_validator
from typing_extensions import Self

from src.domain.exceptions.badge_design_exceptions import BadgeDesignVariantValidationError
from src.domain.models.meetup_detail import MeetupDetailDomainModel


class BadgeRole(StrEnum):
    """Enumeration of supported badge design role variants."""

    SPEAKER = 'speaker'
    PARTICIPANT = 'participant'


class BadgeDesignDomainModel(BaseModel):
    """Pure domain model representing a badge design blueprint.

    :raises BadgeDesignVariantValidationError: When role-specific invariants are violated
    (e.g. speaker badge missing speakers, participant badge carrying speaker data).
    """

    design_id: str
    name: str
    storage_path: str
    role: BadgeRole
    speakers: Optional[list[dict[str, Any]]] = None
    meetup_detail: MeetupDetailDomainModel

    @model_validator(mode='after')
    def __validate_role_invariants(self) -> Self:
        """Enforce role-specific badge design invariants.

        :returns: The validated model instance.
        :rtype: Self
        :raises BadgeDesignVariantValidationError: When the speaker variant has no speakers
            or the participant variant has associated speaker data.
        """
        if self.role == BadgeRole.SPEAKER:
            if not self.speakers:
                raise BadgeDesignVariantValidationError(
                    f"Badge design '{self.design_id}' with role 'speaker' must include at least one speaker."
                )
        elif self.role == BadgeRole.PARTICIPANT:
            if self.speakers is not None:
                raise BadgeDesignVariantValidationError(
                    f"Badge design '{self.design_id}' with role 'participant' must not include speaker data."
                )
        return self
