"""FastAPI dependency injection providers for TechTix integration."""

from src.application.ports.gateways.techtix_gateway_port import TechTixGatewayPort
from src.core.settings import settings
from src.infrastructure.gateway.techtix_http_gateway import (
    TechTixHttpGateway,
)


def get_techtix_gateway() -> TechTixGatewayPort:
    """
    Provide an instance of the TechTixGatewayPort.

    :returns: A configured instance of TechTixHttpGateway.
    :rtype: TechTixGatewayPort
    """
    return TechTixHttpGateway(
        api_base_url=settings.TECHTIX_API_BASE_URL,
        api_key=settings.TECHTIX_API_KEY,
    )
