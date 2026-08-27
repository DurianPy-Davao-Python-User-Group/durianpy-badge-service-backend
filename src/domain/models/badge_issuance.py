"""Badge issuance domain model."""

from typing import Any, Optional

from pydantic import BaseModel

from src.domain.models.meetup_detail import MeetupDetailDomainModel


class BadgeIssuanceDomainModel(BaseModel):
    """Pure domain model representing an issued badge assigned to a user."""

    issuance_id: str
    email: str
    design_id: str
    role: Optional[str] = None
    updated_by: Optional[str] = None
    previous_assignments: Optional[list[dict[str, Any]]] = None
    meetup_detail: Optional[MeetupDetailDomainModel] = None
