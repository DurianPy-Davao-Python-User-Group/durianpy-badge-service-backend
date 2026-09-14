"""Abstract port contract for verifying access tokens and extracting authenticated user domain entities."""

from abc import ABC, abstractmethod

from src.domain.models.authenticated_user import AuthenticatedUser


class TokenVerifierPort(ABC):
    """Outbound port interface for decoding and validating access tokens."""

    @abstractmethod
    def verify(self, token: str) -> AuthenticatedUser:
        """
        Decode and verify an OAuth2 access token, returning the domain AuthenticatedUser.

        :param token: Raw Bearer access token string to verify.
        :type token: str
        :returns: Verified authenticated user domain model containing identity, groups, and scopes.
        :rtype: AuthenticatedUser
        :raises AuthenticationError: If the token is expired, has an invalid signature, or is malformed.
        """
        pass
