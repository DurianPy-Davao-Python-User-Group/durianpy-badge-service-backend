"""Data Transfer Objects (DTOs) for badge issuance operations."""

from typing import Any, Optional

from pydantic import BaseModel

from src.application.dtos.badge_design_dto import MeetupDetailDTO


class UserPortfolioQueryDTO(BaseModel):
    """Query parameter DTO for user portfolio badge searches."""

    email: str
    year: Optional[str] = None


class BadgeIssuanceOutputDTO(BaseModel):
    """Response payload DTO representing an issued user badge."""

    issuance_id: str
    email: str
    design_id: str
    role: Optional[str] = None
    updated_by: Optional[str] = None
    previous_assignments: Optional[list[dict[str, Any]]] = None
    meetup_detail: Optional[MeetupDetailDTO] = None
