"""Badge design domain specific exceptions."""

from src.domain.exceptions.base_exceptions import (
    DomainError,
    EntityNotFoundError,
    RepositoryError,
    StorageServiceError,
)


class BadgeDesignError(DomainError):
    """Base exception for badge design domain operations."""

    pass


class BadgeDesignNotFoundError(EntityNotFoundError, BadgeDesignError):
    """Exception raised when a specific badge design is not found."""

    pass


class BadgeDesignRepositoryError(RepositoryError, BadgeDesignError):
    """Exception raised when a badge design persistence operation fails."""

    pass


class BadgeDesignCreationError(BadgeDesignRepositoryError):
    """Exception raised when persisting a new badge design fails."""

    pass


class BadgeDesignQueryError(BadgeDesignRepositoryError):
    """Exception raised when querying the public badge design catalog fails."""

    pass


class MediaResolutionError(StorageServiceError, BadgeDesignError):
    """Exception raised when resolving asset storage paths to public URLs fails."""

    pass
