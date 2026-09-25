"""HTTP schemas for administrator badge artwork uploads."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class PresignBadgeDesignUploadRequestSchema(BaseModel):
    """Validated request for a WebP badge artwork upload URL."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    meetup_id: UUID
    filename: str = Field(pattern=r'^[A-Za-z0-9][A-Za-z0-9._-]*\.webp$')
    content_type: Literal['image/webp']
    role: Literal['participant', 'speaker']


class PresignBadgeDesignUploadResponseSchema(BaseModel):
    """Signed upload URL and canonical relative storage path."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    upload_url: str
    storage_path: str
