"""Authenticated user domain model representing identity, roles, groups, and token scopes."""

from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """Enumeration of recognized user roles within the system."""

    SUPERADMIN = 'superadmin'
    ADMIN = 'admin'
    USER = 'user'


class AuthenticatedUser(BaseModel):
    """Pure domain model representing an authenticated user identity and claims."""

    user_id: str
    username: str
    groups: list[str] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=list)
    client_id: Optional[str] = None
    raw_claims: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_superadmin(self) -> bool:
        """
        Check if user belongs to the superadmin group (supports 'superadmin' and 'super_admin').

        :returns: True if user has superadmin privileges, False otherwise.
        :rtype: bool
        """
        return UserRole.SUPERADMIN.value in self.groups or 'super_admin' in self.groups

    @property
    def is_admin(self) -> bool:
        """
        Check if user has administrative privileges (admin or superadmin).

        :returns: True if user has admin or superadmin privileges, False otherwise.
        :rtype: bool
        """
        return self.is_superadmin or UserRole.ADMIN.value in self.groups

    @property
    def is_google_user(self) -> bool:
        """
        Check if user authenticated via Google federation based on assigned group or username prefix.

        :returns: True if username starts with 'google_' or user belongs to a Google IdP group.
        :rtype: bool
        """
        return self.google_group is not None or self.username.lower().startswith('google_')

    @property
    def google_group(self) -> Optional[str]:
        """
        Retrieve the Google federation group name if assigned.

        :returns: The Google group string or None if not found.
        :rtype: Optional[str]
        """
        for group in self.groups:
            group_lower = group.lower()
            if group_lower.endswith('_google') or group_lower.startswith('google_') or group_lower == 'google':
                return group
        return None

    @property
    def is_regular_user(self) -> bool:
        """
        Check if user is a regular attendee without administrative privileges.

        :returns: True if user does not hold admin or superadmin roles, False otherwise.
        :rtype: bool
        """
        return not self.is_admin

    def has_role(self, role: Union[UserRole, str]) -> bool:
        """
        Evaluate whether the user possesses the specified role or group membership.

        :param role: Target role enum or group string to check.
        :type role: Union[UserRole, str]
        :returns: True if authorized for the specified role, False otherwise.
        :rtype: bool
        """
        role_val = role.value if isinstance(role, UserRole) else role
        if role_val in (UserRole.SUPERADMIN.value, 'super_admin'):
            return self.is_superadmin
        if role_val == UserRole.ADMIN.value:
            return self.is_admin
        if role_val == UserRole.USER.value:
            return True
        return role_val in self.groups

    def has_any_role(self, *roles: Union[UserRole, str]) -> bool:
        """
        Evaluate whether the user holds at least one of the specified roles or groups.

        :param roles: Roles or group strings to evaluate.
        :type roles: Union[UserRole, str]
        :returns: True if any role matches, False otherwise.
        :rtype: bool
        """
        return any(self.has_role(role) for role in roles)

    def has_scope(self, scope: str) -> bool:
        """
        Check if the user token contains a specific OAuth2 scope.

        :param scope: The scope identifier to check.
        :type scope: str
        :returns: True if scope is present, False otherwise.
        :rtype: bool
        """
        return scope in self.scopes

    def has_all_scopes(self, *scopes: str) -> bool:
        """
        Check if the user token contains all specified OAuth2 scopes.

        :param scopes: Scope identifiers to evaluate.
        :type scopes: str
        :returns: True if all scopes are present, False otherwise.
        :rtype: bool
        """
        return all(self.has_scope(scope) for scope in scopes)
