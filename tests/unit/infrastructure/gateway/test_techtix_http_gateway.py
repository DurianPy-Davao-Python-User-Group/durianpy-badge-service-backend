"""Unit tests for the TechTix HTTP Gateway."""

import httpx
import pytest

from src.application.dtos.badge_design_dto import MeetupDetailDTO
from src.domain.exceptions.techtix_exceptions import (
    TechTixEventNotFoundError,
    TechTixGatewayError,
    TechTixGatewayTimeout,
)
from src.infrastructure.gateway.techtix_http_gateway import TechTixHttpGateway


def test_get_meetup_details_maps_only_essential_fields() -> None:
    """Verify only the required fields are extracted into the DTO."""

    def _handler(request: httpx.Request) -> httpx.Response:
        assert request.url == 'https://api.techtix.local/events/evt-123'
        payload = {
            'eventId': 'evt-123',
            'name': 'DurianPy September 2026 Meetup',
            'startDate': '2026-09-26T18:00:00.000Z',
            'venue': 'Davao City Tech Hub',
            'ticketTypes': [{'name': 'General Admission'}],
            'gcashNumber': '09171234567',
            'konfhubApiKey': 'super-secret',
            'platformFee': 99,
            'certificateTemplate': 'tpl-1',
        }
        return httpx.Response(200, json=payload)

    client = httpx.Client(transport=httpx.MockTransport(_handler), base_url='https://api.techtix.local')
    gateway = TechTixHttpGateway(
        api_base_url='https://api.techtix.local',
        client=client,
    )

    meetup = gateway.get_meetup_details('evt-123')

    assert meetup == MeetupDetailDTO(
        meetup_id='evt-123',
        name='DurianPy September 2026 Meetup',
        date='2026-09-26T18:00:00.000Z',
        venue='Davao City Tech Hub',
    )


def test_get_meetup_details_raises_not_found_for_404() -> None:
    """Verify 404 responses map to the domain not-found error."""

    def _handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={'message': 'Event with entryId evt-123 does not exist.'})

    client = httpx.Client(transport=httpx.MockTransport(_handler), base_url='https://api.techtix.local')
    gateway = TechTixHttpGateway(
        api_base_url='https://api.techtix.local',
        api_key='secret-key-xyz',
        client=client,
    )

    with pytest.raises(TechTixEventNotFoundError, match='evt-123'):
        gateway.get_meetup_details('evt-123')


def test_get_meetup_details_raises_gateway_error_for_5xx() -> None:
    """Verify 5xx responses map to the domain gateway error."""

    def _handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={'message': 'upstream unavailable'})

    client = httpx.Client(transport=httpx.MockTransport(_handler), base_url='https://api.techtix.local')
    gateway = TechTixHttpGateway(
        api_base_url='https://api.techtix.local',
        client=client,
    )

    with pytest.raises(TechTixGatewayError, match='TechTix'):
        gateway.get_meetup_details('evt-123')


def test_get_meetup_details_raises_gateway_error_for_timeout() -> None:
    """Verify timeout and network failures are translated to the domain gateway error."""

    def _handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout('Request timed out')

    client = httpx.Client(transport=httpx.MockTransport(_handler), base_url='https://api.techtix.local')
    gateway = TechTixHttpGateway(
        api_base_url='https://api.techtix.local',
        client=client,
    )

    with pytest.raises(TechTixGatewayTimeout, match='timed out|failed'):
        gateway.get_meetup_details('evt-123')
