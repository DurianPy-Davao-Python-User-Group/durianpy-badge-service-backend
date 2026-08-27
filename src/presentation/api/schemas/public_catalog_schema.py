"""HTTP schemas for public catalog discovery API endpoints."""

from typing import Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class PublicBadgeDesignItemSchema(BaseModel):
    """Schema representing an individual public badge design item."""

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )

    design_id: str
    meetup_name: Optional[str] = None
    meetup_date: Optional[str] = None
    venue: Optional[str] = None
    name: str
    design_url: str
    role: str


class PublicCatalogResponseSchema(BaseModel):
    """Envelope schema for public catalog response payload."""

    data: list[PublicBadgeDesignItemSchema]
