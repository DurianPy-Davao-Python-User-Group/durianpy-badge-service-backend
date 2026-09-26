"""Data Transfer Objects (DTOs) for badge design operations."""

from typing import Any, Optional

from pydantic import BaseModel


class MeetupDetailDTO(BaseModel):
    """DTO representing meetup details."""

    meetup_id: str
    name: Optional[str] = None
    date: Optional[str] = None
    venue: Optional[str] = None


class CreateBadgeDesignInputDTO(BaseModel):
    """Input DTO for creating a badge design blueprint."""

    name: str
    storage_path: str
    role: str
    year: str
    iso_date: str
    created_by: str
    meetup_detail: MeetupDetailDTO
    speakers: Optional[list[dict[str, Any]]] = None


class PublicCatalogQueryDTO(BaseModel):
    """Query parameter DTO for public catalog design searches."""

    year: str
    year_gt: Optional[str] = None
    year_lt: Optional[str] = None


class BadgeDesignOutputDTO(BaseModel):
    """Response payload DTO representing a badge design."""

    design_id: str
    name: str
    storage_path: str
    role: str
    meetup_detail: MeetupDetailDTO
    speakers: Optional[list[dict[str, Any]]] = None


class PublicBadgeDesignOutputDTO(BaseModel):
    """Output DTO representing a public catalog badge design with resolved URL."""

    design_id: str
    meetup_name: Optional[str] = None
    meetup_date: Optional[str] = None
    venue: Optional[str] = None
    name: str
    design_url: str
    role: str


class PresignUploadInputDTO(BaseModel):
    """Input values for requesting a badge artwork upload URL."""

    meetup_id: str
    filename: str
    content_type: str
    role: str


class PresignUploadOutputDTO(BaseModel):
    """Generated upload URL and relative badge artwork storage path."""

    upload_url: str
    storage_path: str
