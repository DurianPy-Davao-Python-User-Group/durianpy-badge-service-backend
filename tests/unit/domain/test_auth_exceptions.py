"""Unit tests for authentication and authorization domain exceptions."""

from src.domain.exceptions.auth_exceptions import (
    AuthenticationError,
    AuthError,
    AuthorizationError,
)
from src.domain.exceptions.base_exceptions import DomainError


def test_auth_exceptions_hierarchy_and_codes() -> None:
    """Verify auth exception inheritance, default messages, and machine-readable codes."""
    auth_err = AuthError('Base auth failure', code='CUSTOM_AUTH_CODE')
    assert isinstance(auth_err, DomainError)
    assert auth_err.message == 'Base auth failure'
    assert auth_err.code == 'CUSTOM_AUTH_CODE'

    default_auth_err = AuthError()
    assert default_auth_err.code == 'AuthError'

    authn_err = AuthenticationError()
    assert isinstance(authn_err, AuthError)
    assert authn_err.code == 'AUTHENTICATION_FAILED'
    assert 'Authentication credentials' in authn_err.message

    authz_err = AuthorizationError()
    assert isinstance(authz_err, AuthError)
    assert authz_err.code == 'INSUFFICIENT_PERMISSIONS'
    assert 'User does not possess sufficient privileges' in authz_err.message
