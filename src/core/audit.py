"""Core audit module providing reusable Pydantic audit mixins and utilities."""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


def current_utc_time() -> datetime:
    """
    Return the current timestamp in UTC.

    :returns: Current UTC datetime instance.
    :rtype: datetime
    """
    return datetime.now(timezone.utc)


class DurianPyAuditMixin(BaseModel):
    """Mixin for common audit metadata attributes across Pydantic models."""

    durianpy_created_at: datetime = Field(default_factory=current_utc_time)
    durianpy_updated_at: datetime = Field(default_factory=current_utc_time)
    durianpy_created_by: str
    durianpy_updated_by: Optional[str] = None
