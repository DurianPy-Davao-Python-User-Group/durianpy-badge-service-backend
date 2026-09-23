"""TechTix integration domain exceptions."""

from src.domain.exceptions.base_exceptions import (
    DomainError,
    EntityNotFoundError,
    GatewayTimeoutError,
)


class TechTixGatewayError(DomainError):
    """Exception raised when communication with the TechTix external service fails."""

    pass


class TechTixEventNotFoundError(EntityNotFoundError, TechTixGatewayError):
    """Exception raised when a requested event cannot be found in TechTix."""

    pass


class TechTixGatewayTimeout(GatewayTimeoutError, TechTixGatewayError):
    """Exception raised when a requested event cannot be found in TechTix."""

    pass
