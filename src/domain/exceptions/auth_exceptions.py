"""Authentication and authorization domain-specific exceptions."""

from typing import Optional

from src.domain.exceptions.base_exceptions import DomainError


class AuthError(DomainError):
    """Base exception for authentication and authorization failures."""

    def __init__(
        self,
        message: str = 'An authentication or authorization error occurred.',
        code: Optional[str] = None,
    ) -> None:
        """
        Initialize auth error.

        :param message: Human-readable error description.
        :type message: str
        :param code: Optional machine-readable error code identifier.
        :type code: Optional[str]
        """
        super().__init__(message=message, code=code)


class AuthenticationError(AuthError):
    """Exception raised when user authentication fails (e.g. invalid, expired, or missing token)."""

    def __init__(
        self,
        message: str = 'Authentication credentials were not provided or are invalid.',
        code: Optional[str] = None,
    ) -> None:
        """
        Initialize authentication error.

        :param message: Human-readable error description.
        :type message: str
        :param code: Optional machine-readable error code identifier.
        :type code: Optional[str]
        """
        super().__init__(message=message, code=code or 'AUTHENTICATION_FAILED')


class AuthorizationError(AuthError):
    """Exception raised when an authenticated user lacks required permissions, groups, or scopes."""

    def __init__(
        self,
        message: str = 'User does not possess sufficient privileges to perform this action.',
        code: Optional[str] = None,
    ) -> None:
        """
        Initialize authorization error.

        :param message: Human-readable error description.
        :type message: str
        :param code: Optional machine-readable error code identifier.
        :type code: Optional[str]
        """
        super().__init__(message=message, code=code or 'INSUFFICIENT_PERMISSIONS')
