"""Meetup detail domain model."""

from typing import Optional

from pydantic import BaseModel


class MeetupDetailDomainModel(BaseModel):
    """Domain model representing meetup event details."""

    meetup_id: str
    name: Optional[str] = None
    date: Optional[str] = None
    venue: Optional[str] = None
