"""Unit tests for AuthenticatedUser domain entity and UserRole enum."""

from src.domain.models.authenticated_user import AuthenticatedUser, UserRole


def test_superadmin_user_properties() -> None:
    """Verify role checks and permissions for superadmin user."""
    user = AuthenticatedUser(
        user_id='sub-super-1',
        username='superadmin_user',
        groups=['superadmin'],
        scopes=['openid', 'profile'],
    )
    assert user.is_superadmin is True
    assert user.is_admin is True
    assert user.is_regular_user is False
    assert user.is_google_user is False
    assert user.google_group is None
    assert user.has_role(UserRole.SUPERADMIN) is True
    assert user.has_role(UserRole.ADMIN) is True
    assert user.has_role(UserRole.USER) is True
    assert user.has_any_role(UserRole.ADMIN, 'other_group') is True


def test_admin_user_properties() -> None:
    """Verify role checks and permissions for admin user."""
    user = AuthenticatedUser(
        user_id='sub-admin-1',
        username='admin_user',
        groups=['admin'],
        scopes=['openid'],
    )
    assert user.is_superadmin is False
    assert user.is_admin is True
    assert user.is_regular_user is False
    assert user.is_google_user is False
    assert user.has_role(UserRole.SUPERADMIN) is False
    assert user.has_role(UserRole.ADMIN) is True
    assert user.has_role(UserRole.USER) is True


def test_google_authenticated_regular_user() -> None:
    """Verify regular user who authenticated via Google federation with pool group."""
    user = AuthenticatedUser(
        user_id='sub-google-1',
        username='google_104767069296039333070',
        groups=['ap-southeast-1_jJusvTlat_Google'],
        scopes=['openid', 'email', 'profile'],
    )
    assert user.is_superadmin is False
    assert user.is_admin is False
    assert user.is_regular_user is True
    assert user.is_google_user is True
    assert user.google_group == 'ap-southeast-1_jJusvTlat_Google'
    assert user.has_role(UserRole.SUPERADMIN) is False
    assert user.has_role(UserRole.ADMIN) is False
    assert user.has_role(UserRole.USER) is True
    assert user.has_role('ap-southeast-1_jJusvTlat_Google') is True
    assert user.has_role('unknown_group') is False


def test_google_authenticated_user_by_username_only() -> None:
    """Verify user with google_ username prefix but no Google group assigned."""
    user = AuthenticatedUser(
        user_id='sub-google-2',
        username='google_104767069296039333070',
        groups=[],
        scopes=['openid'],
    )
    assert user.is_google_user is True
    assert user.google_group is None
    assert user.is_regular_user is True


def test_superadmin_user_with_underscore_group() -> None:
    """Verify superadmin recognition with 'super_admin' group naming."""
    user = AuthenticatedUser(
        user_id='sub-super-2',
        username='super_admin_user',
        groups=['super_admin', 'admin'],
        scopes=['openid'],
    )
    assert user.is_superadmin is True
    assert user.is_admin is True
    assert user.has_role(UserRole.SUPERADMIN) is True
    assert user.has_role('super_admin') is True


def test_regular_user_no_groups() -> None:
    """Verify regular attendee with no groups assigned."""
    user = AuthenticatedUser(
        user_id='sub-user-1',
        username='regular_attendee',
        groups=[],
        scopes=['openid'],
    )
    assert user.is_superadmin is False
    assert user.is_admin is False
    assert user.is_regular_user is True
    assert user.is_google_user is False
    assert user.google_group is None
    assert user.has_role(UserRole.USER) is True
    assert user.has_any_role(UserRole.ADMIN, UserRole.SUPERADMIN) is False


def test_token_scope_validation() -> None:
    """Verify has_scope and has_all_scopes methods."""
    user = AuthenticatedUser(
        user_id='sub-scope-1',
        username='scoped_user',
        scopes=['openid', 'email', 'designs:read'],
    )
    assert user.has_scope('openid') is True
    assert user.has_scope('email') is True
    assert user.has_scope('designs:read') is True
    assert user.has_scope('designs:write') is False
    assert user.has_all_scopes('openid', 'designs:read') is True
    assert user.has_all_scopes('openid', 'designs:write') is False
