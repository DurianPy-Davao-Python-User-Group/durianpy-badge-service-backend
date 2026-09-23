"""TechTix HTTP Gateway implementation."""

from __future__ import annotations

from typing import Optional

import httpx

from src.application.dtos.badge_design_dto import MeetupDetailDTO
from src.application.ports.gateways.techtix_gateway_port import TechTixGatewayPort
from src.core.logging import logger, mask_string
from src.core.settings import settings
from src.domain.exceptions.techtix_exceptions import (
    TechTixEventNotFoundError,
    TechTixGatewayError,
)


class TechTixHttpGateway(TechTixGatewayPort):
    """HTTP-based adapter for the TechTix external gateway port."""

    def __init__(
        self,
        api_base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        client: Optional[httpx.Client] = None,
        base_url: Optional[str] = None,
    ) -> None:
        """
        Initialize the HTTP gateway.

        :param api_base_url: Optional TechTix API base URL.
        :type api_base_url: Optional[str]
        :param api_key: Optional TechTix API key.
        :type api_key: Optional[str]
        :param client: Optional pre-configured HTTP client with test transport support.
        :type client: Optional[httpx.Client]
        :param base_url: Backward-compatible alias for the API base URL.
        :type base_url: Optional[str]
        """
        resolved_base_url = api_base_url or base_url or settings.TECHTIX_API_BASE_URL
        self.__api_base_url = resolved_base_url.rstrip('/')
        self.__api_key = api_key if api_key is not None else settings.TECHTIX_API_KEY
        self.__client = client or httpx.Client(base_url=self.__api_base_url, timeout=10.0)

    def get_meetup_details(self, meetup_id: str) -> MeetupDetailDTO:
        """
        Retrieve verified meetup details from TechTix by event ID.

        :param meetup_id: The unique identifier (entryId) of the TechTix event.
        :type meetup_id: str
        :returns: Essential meetup details mapped to a DTO.
        :rtype: MeetupDetailDTO
        :raises TechTixEventNotFoundError: If the event does not exist (404).
        :raises TechTixGatewayError: If communication with the gateway fails.
        """
        if not meetup_id or not isinstance(meetup_id, str):
            raise TechTixGatewayError('TechTix meetup identifier must be a non-empty string.')

        url = f'/events/admin/{meetup_id}'
        headers = {'Authorization': f'Bearer {self.__api_key}'}

        logger.info(
            "Fetching TechTix meetup '%s' '%s' using auth header '%s'",
            self.__api_base_url,
            url,
            mask_string(headers['Authorization']),
        )

        try:
            response = self.__client.get(url, headers=headers)
        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPError) as exc:
            logger.error("TechTix meetup '%s' request failed: %s", meetup_id, exc)
            raise TechTixGatewayError(f'TechTix request for meetup {meetup_id} failed: {exc}') from exc

        if response.status_code == 404:
            logger.warning("TechTix meetup '%s' was not found.", meetup_id)
            raise TechTixEventNotFoundError(f'Event with entryId {meetup_id} does not exist.')

        if 500 <= response.status_code < 600:
            logger.error(
                "TechTix meetup '%s' returned server error %s.",
                meetup_id,
                response.status_code,
            )
            raise TechTixGatewayError(f'TechTix gateway error for meetup {meetup_id}; status {response.status_code}.')

        if response.status_code != 200:
            logger.error(
                "TechTix meetup '%s' returned unexpected HTTP status %s.",
                meetup_id,
                response.status_code,
            )
            raise TechTixGatewayError(f'TechTix gateway error for meetup {meetup_id}; status {response.status_code}.')

        try:
            payload = response.json()
        except ValueError as exc:
            logger.error("TechTix meetup '%s' returned invalid JSON.", meetup_id)
            raise TechTixGatewayError(f'TechTix response payload for meetup {meetup_id} is invalid.') from exc

        if not isinstance(payload, dict):
            logger.error("TechTix meetup '%s' returned a non-object payload.", meetup_id)
            raise TechTixGatewayError(f'TechTix response payload for meetup {meetup_id} is invalid.')

        meetup_detail = MeetupDetailDTO(
            meetup_id=str(payload.get('eventId') or payload.get('entryId') or payload.get('meetupId') or meetup_id),
            name=payload.get('name'),
            date=payload.get('startDate'),
            venue=payload.get('venue'),
        )

        logger.info(
            "Mapped TechTix meetup '%s' to DTO with name '%s' at venue '%s'.",
            meetup_detail.meetup_id,
            meetup_detail.name,
            meetup_detail.venue,
        )
        return meetup_detail
