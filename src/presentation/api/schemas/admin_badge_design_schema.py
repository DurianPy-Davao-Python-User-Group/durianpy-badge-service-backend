"""HTTP schemas for administrator badge design creation and artwork upload endpoints."""

from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field
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


class SpeakerItemSchema(BaseModel):
    """Schema representing a single speaker associated with a badge design."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    name: str = Field(min_length=1, description='Full display name of the speaker.')
    talk_title: Optional[str] = Field(default=None, description='Title of the speaker talk or session.')
    email: Optional[EmailStr] = Field(default=None, description='Contact email address of the speaker.')

    def to_dict(self) -> dict[str, Any]:
        """Serialise the speaker item to a plain dictionary including any extra fields.

        :returns: Speaker data as a plain dictionary.
        :rtype: dict[str, Any]
        """
        return self.model_dump(by_alias=False)


class CreateBadgeDesignRequestSchema(BaseModel):
    """Validated HTTP request body for creating a new badge design blueprint.

    ``meetupId`` is resolved against TechTix — any additional meetup metadata
    (name, date, venue) is authoritative from the gateway, not the client.
    ``year`` and ``iso_date`` are derived server-side from the UTC wall-clock at
    creation time and therefore do not appear in the request body.
    """

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    meetup_id: UUID = Field(description='Unique TechTix event identifier (entryId) to resolve against the gateway.')
    name: str = Field(min_length=1, description='Display name of the badge design.')
    storage_path: str = Field(
        min_length=1,
        description='Relative bucket path to the badge artwork (e.g. designs/<meetupId>/speaker_2026-09-12T10-40-00Z.webp).',
    )
    role: Literal['participant', 'speaker'] = Field(description="Badge role variant: 'participant' or 'speaker'.")
    speakers: Optional[list[SpeakerItemSchema]] = Field(
        default=None,
        description="Speaker list — required for 'speaker' role designs, must be omitted for 'participant'.",
    )


class CreateBadgeDesignResponseSchema(BaseModel):
    """HTTP response schema for a successfully created badge design."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    design_id: str = Field(description='Unique identifier of the persisted badge design.')
    meetup_id: str = Field(description='TechTix event identifier the badge design belongs to.')
    name: str = Field(description='Display name of the badge design.')
    design_url: str = Field(description='Resolved CloudFront public URL of the badge artwork.')
    role: str = Field(description="Badge role variant ('participant' or 'speaker').")
    speakers: Optional[list[SpeakerItemSchema]] = Field(
        default=None,
        description='Speaker list associated with the badge design.',
    )
