"""Domain exceptions package exporting base and entity-specific domain exceptions."""

from src.domain.exceptions.auth_exceptions import (
    AuthenticationError,
    AuthError,
    AuthorizationError,
)
from src.domain.exceptions.badge_design_exceptions import (
    BadgeDesignCreationError,
    BadgeDesignError,
    BadgeDesignNotFoundError,
    BadgeDesignQueryError,
    BadgeDesignRepositoryError,
    MediaResolutionError,
    StoragePresignError,
)
from src.domain.exceptions.base_exceptions import (
    DomainError,
    EntityNotFoundError,
    EntityValidationError,
    RepositoryError,
    StorageServiceError,
)

__all__ = [
    'AuthError',
    'AuthenticationError',
    'AuthorizationError',
    'DomainError',
    'EntityNotFoundError',
    'EntityValidationError',
    'RepositoryError',
    'StorageServiceError',
    'BadgeDesignError',
    'BadgeDesignNotFoundError',
    'BadgeDesignRepositoryError',
    'BadgeDesignCreationError',
    'BadgeDesignQueryError',
    'MediaResolutionError',
    'StoragePresignError',
]
