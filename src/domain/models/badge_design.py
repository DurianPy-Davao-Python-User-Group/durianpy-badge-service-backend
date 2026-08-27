"""Badge design domain model."""

from typing import Any, Optional

from pydantic import BaseModel

from src.domain.models.meetup_detail import MeetupDetailDomainModel


class BadgeDesignDomainModel(BaseModel):
    """Pure domain model representing a badge design blueprint."""

    design_id: str
    name: str
    storage_path: str
    role: str
    speakers: Optional[list[dict[str, Any]]] = None
    meetup_detail: MeetupDetailDomainModel
