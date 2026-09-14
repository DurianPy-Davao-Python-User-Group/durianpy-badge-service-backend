"""FastAPI authentication and authorization dependency providers."""

from typing import Callable, Optional, Union

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.application.ports.security.token_verifier_port import TokenVerifierPort
from src.domain.exceptions.auth_exceptions import (
    AuthenticationError,
    AuthorizationError,
)
from src.domain.models.authenticated_user import AuthenticatedUser, UserRole
from src.infrastructure.security.cognito_token_verifier import (
    CognitoTokenVerifier,
)

__security = HTTPBearer(auto_error=False)


def get_token_verifier() -> TokenVerifierPort:
    """
    Provide concrete TokenVerifierPort implementation.

    :returns: Instance of CognitoTokenVerifier.
    :rtype: TokenVerifierPort
    """
    return CognitoTokenVerifier()


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(__security),
    verifier: TokenVerifierPort = Depends(get_token_verifier),
) -> AuthenticatedUser:
    """
    FastAPI dependency extracting and verifying the Bearer token from the Authorization header.

    :param credentials: Extracted HTTP Bearer credentials from the request.
    :type credentials: Optional[HTTPAuthorizationCredentials]
    :param verifier: Injected token verifier port.
    :type verifier: TokenVerifierPort
    :returns: Authenticated user domain entity containing user identity, groups, and scopes.
    :rtype: AuthenticatedUser
    :raises AuthenticationError: If the Authorization header is missing, malformed, or invalid.
    """
    if credentials is None or not credentials.credentials:
        raise AuthenticationError('Missing or empty Authorization header.')

    if credentials.scheme.lower() != 'bearer':
        raise AuthenticationError("Authorization scheme must be 'Bearer'.")

    return verifier.verify(credentials.credentials)


def require_roles(*roles: Union[UserRole, str]) -> Callable[..., AuthenticatedUser]:
    """
    Create a FastAPI dependency that verifies the authenticated user holds at least one required role.

    :param roles: Roles or group names allowed to access the endpoint.
    :type roles: Union[UserRole, str]
    :returns: Dependency function returning the verified AuthenticatedUser.
    :rtype: Callable[..., AuthenticatedUser]
    """

    def __role_checker(
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        """
        Verify that the authenticated user possesses one of the allowed roles.

        :param current_user: Injected authenticated user.
        :type current_user: AuthenticatedUser
        :returns: The verified AuthenticatedUser.
        :rtype: AuthenticatedUser
        :raises AuthorizationError: If the user lacks the required roles.
        """
        if not current_user.has_any_role(*roles):
            required_str = ', '.join(r.value if isinstance(r, UserRole) else r for r in roles)
            raise AuthorizationError(f'User does not hold any of the required roles: {required_str}')
        return current_user

    return __role_checker


def require_scopes(*scopes: str) -> Callable[..., AuthenticatedUser]:
    """
    Create a FastAPI dependency that verifies the user token contains all required scopes.

    :param scopes: Scope strings required to access the endpoint.
    :type scopes: str
    :returns: Dependency function returning the verified AuthenticatedUser.
    :rtype: Callable[..., AuthenticatedUser]
    """

    def __scope_checker(
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        """
        Verify that the user token possesses all required scopes.

        :param current_user: Injected authenticated user.
        :type current_user: AuthenticatedUser
        :returns: The verified AuthenticatedUser.
        :rtype: AuthenticatedUser
        :raises AuthorizationError: If one or more required scopes are missing.
        """
        missing_scopes = [s for s in scopes if not current_user.has_scope(s)]
        if missing_scopes:
            raise AuthorizationError(f'Missing required scope(s): {", ".join(missing_scopes)}')
        return current_user

    return __scope_checker


require_admin = require_roles(UserRole.ADMIN, UserRole.SUPERADMIN, 'super_admin')
require_superadmin = require_roles(UserRole.SUPERADMIN, 'super_admin')
