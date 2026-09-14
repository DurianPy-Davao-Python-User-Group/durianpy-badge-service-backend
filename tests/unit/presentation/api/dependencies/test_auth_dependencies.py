"""Unit tests for FastAPI authentication and authorization dependencies."""

from unittest.mock import MagicMock

import pytest
from fastapi import Depends, FastAPI
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient

from src.application.ports.security.token_verifier_port import TokenVerifierPort
from src.domain.exceptions.auth_exceptions import (
    AuthenticationError,
    AuthorizationError,
)
from src.domain.models.authenticated_user import AuthenticatedUser, UserRole
from src.infrastructure.security.cognito_token_verifier import (
    CognitoTokenVerifier,
)
from src.presentation.api.dependencies.auth_dependencies import (
    get_current_user,
    get_token_verifier,
    require_admin,
    require_roles,
    require_scopes,
    require_superadmin,
)
from src.presentation.api.exception_handlers import (
    register_domain_exception_handlers,
)


def test_get_token_verifier_returns_instance() -> None:
    """Verify get_token_verifier provides a concrete CognitoTokenVerifier."""
    verifier = get_token_verifier()
    assert isinstance(verifier, CognitoTokenVerifier)


def test_get_current_user_missing_credentials() -> None:
    """Verify AuthenticationError when Authorization header is absent."""
    verifier = MagicMock(spec=TokenVerifierPort)
    with pytest.raises(AuthenticationError, match='Missing or empty Authorization header'):
        get_current_user(credentials=None, verifier=verifier)


def test_get_current_user_empty_token() -> None:
    """Verify AuthenticationError when credentials token is empty."""
    verifier = MagicMock(spec=TokenVerifierPort)
    creds = HTTPAuthorizationCredentials(scheme='Bearer', credentials='')
    with pytest.raises(AuthenticationError, match='Missing or empty Authorization header'):
        get_current_user(credentials=creds, verifier=verifier)


def test_get_current_user_invalid_scheme() -> None:
    """Verify AuthenticationError when scheme is not Bearer."""
    verifier = MagicMock(spec=TokenVerifierPort)
    creds = HTTPAuthorizationCredentials(scheme='Basic', credentials='secret-token')
    with pytest.raises(AuthenticationError, match="Authorization scheme must be 'Bearer'"):
        get_current_user(credentials=creds, verifier=verifier)


def test_get_current_user_successful_verification() -> None:
    """Verify successful verification delegates to TokenVerifierPort."""
    mock_user = AuthenticatedUser(
        user_id='sub-123',
        username='test_user',
        groups=['admin'],
        scopes=['openid'],
    )
    verifier = MagicMock(spec=TokenVerifierPort)
    verifier.verify.return_value = mock_user

    creds = HTTPAuthorizationCredentials(scheme='Bearer', credentials='valid-token-str')
    user = get_current_user(credentials=creds, verifier=verifier)

    assert user == mock_user
    verifier.verify.assert_called_once_with('valid-token-str')


def test_require_roles_success_and_failure() -> None:
    """Verify require_roles dependency factory checks user roles."""
    checker = require_roles(UserRole.ADMIN, 'moderator')

    authorized_user = AuthenticatedUser(
        user_id='sub-admin',
        username='admin',
        groups=['admin'],
    )
    assert checker(current_user=authorized_user) == authorized_user

    unauthorized_user = AuthenticatedUser(
        user_id='sub-google-regular',
        username='regular',
        groups=['google_12345'],
    )
    with pytest.raises(AuthorizationError, match='User does not hold any of the required roles'):
        checker(current_user=unauthorized_user)


def test_require_scopes_success_and_failure() -> None:
    """Verify require_scopes dependency factory checks user scopes."""
    checker = require_scopes('designs:read', 'designs:write')

    authorized_user = AuthenticatedUser(
        user_id='sub-scoped',
        username='scoped_user',
        scopes=['designs:read', 'designs:write', 'openid'],
    )
    assert checker(current_user=authorized_user) == authorized_user

    missing_scope_user = AuthenticatedUser(
        user_id='sub-partial',
        username='partial_user',
        scopes=['designs:read'],
    )
    with pytest.raises(AuthorizationError, match='Missing required scope.*designs:write'):
        checker(current_user=missing_scope_user)


def test_auth_dependencies_integration_with_test_client() -> None:
    """Verify complete HTTP request authentication, role enforcement, and 401/403 status responses."""
    app = FastAPI()
    register_domain_exception_handlers(app)

    mock_verifier = MagicMock(spec=TokenVerifierPort)
    app.dependency_overrides[get_token_verifier] = lambda: mock_verifier

    @app.get('/api/me')
    def get_me(user: AuthenticatedUser = Depends(get_current_user)):
        return {'user_id': user.user_id, 'username': user.username}

    @app.get('/api/admin')
    def admin_only(user: AuthenticatedUser = Depends(require_admin)):
        return {'status': 'admin-access', 'user_id': user.user_id}

    @app.get('/api/superadmin')
    def superadmin_only(user: AuthenticatedUser = Depends(require_superadmin)):
        return {'status': 'superadmin-access', 'user_id': user.user_id}

    client = TestClient(app, raise_server_exceptions=False)

    # 1. Missing Authorization header -> 401
    res_no_auth = client.get('/api/me')
    assert res_no_auth.status_code == 401
    assert res_no_auth.json()['error']['code'] == 'AUTHENTICATION_FAILED'
    assert 'WWW-Authenticate' in res_no_auth.headers

    # 2. Regular Google user accessing /api/me -> 200
    regular_google_user = AuthenticatedUser(
        user_id='sub-google-1',
        username='google_user',
        groups=['google_99999'],
        scopes=['openid'],
    )
    mock_verifier.verify.return_value = regular_google_user

    res_regular = client.get('/api/me', headers={'Authorization': 'Bearer test-google-token'})
    assert res_regular.status_code == 200
    assert res_regular.json() == {'user_id': 'sub-google-1', 'username': 'google_user'}

    # 3. Regular Google user accessing /api/admin -> 403 Forbidden
    res_forbidden_admin = client.get('/api/admin', headers={'Authorization': 'Bearer test-google-token'})
    assert res_forbidden_admin.status_code == 403
    assert res_forbidden_admin.json()['error']['code'] == 'INSUFFICIENT_PERMISSIONS'
    assert 'Bearer error="insufficient_scope"' in res_forbidden_admin.headers.get('WWW-Authenticate', '')

    # 4. Admin user accessing /api/admin -> 200 OK
    admin_user = AuthenticatedUser(
        user_id='sub-admin-1',
        username='admin_user',
        groups=['admin'],
    )
    mock_verifier.verify.return_value = admin_user

    res_admin = client.get('/api/admin', headers={'Authorization': 'Bearer test-admin-token'})
    assert res_admin.status_code == 200
    assert res_admin.json()['status'] == 'admin-access'

    # 5. Admin user accessing /api/superadmin -> 403 Forbidden
    res_forbidden_super = client.get('/api/superadmin', headers={'Authorization': 'Bearer test-admin-token'})
    assert res_forbidden_super.status_code == 403
    assert res_forbidden_super.json()['error']['code'] == 'INSUFFICIENT_PERMISSIONS'

    # 6. Superadmin user accessing /api/superadmin -> 200 OK
    superadmin_user = AuthenticatedUser(
        user_id='sub-super-1',
        username='super_user',
        groups=['superadmin'],
    )
    mock_verifier.verify.return_value = superadmin_user

    res_super = client.get('/api/superadmin', headers={'Authorization': 'Bearer test-super-token'})
    assert res_super.status_code == 200
    assert res_super.json()['status'] == 'superadmin-access'
