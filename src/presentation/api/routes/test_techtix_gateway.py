"""Test route for the TechTix gateway dependency."""

from fastapi import APIRouter, Depends

from src.application.dtos.badge_design_dto import MeetupDetailDTO
from src.application.ports.gateways.techtix_gateway_port import TechTixGatewayPort
from src.presentation.api.dependencies.techtix_dependencies import get_techtix_gateway

router = APIRouter(prefix='/api/techtix', tags=['Techtix Catalog'])


@router.get(
    '/events/{meetup_id}',
    response_model=MeetupDetailDTO,
    status_code=200,
    summary='Test TechTix Gateway',
    description='Fetch one TechTix event through the injected gateway dependency.',
)
def get_techtix_event(
    meetup_id: str,
    gateway: TechTixGatewayPort = Depends(get_techtix_gateway),
) -> MeetupDetailDTO:
    """
    Fetch one event through the injected TechTix gateway.

    :param meetup_id: TechTix event identifier.
    :type meetup_id: str
    :param gateway: Injected TechTix gateway port.
    :type gateway: TechTixGatewayPort
    :returns: Mapped TechTix meetup details.
    :rtype: MeetupDetailDTO
    """
    return gateway.get_meetup_details(meetup_id)
