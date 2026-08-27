"""Base domain exception hierarchies."""

from typing import Optional


class DomainError(Exception):
    """Base exception for all business domain errors."""

    def __init__(self, message: str = 'A domain error occurred.', code: Optional[str] = None) -> None:
        """
        Initialize base domain error.

        :param message: Human-readable error description.
        :type message: str
        :param code: Optional machine-readable error code identifier.
        :type code: Optional[str]
        """
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__


class EntityNotFoundError(DomainError):
    """Exception raised when a requested domain entity cannot be found."""

    pass


class EntityValidationError(DomainError):
    """Exception raised when domain business invariants or validation rules fail."""

    pass


class RepositoryError(DomainError):
    """Exception raised when a persistence operation fails across infrastructure boundaries."""

    pass


class StorageServiceError(DomainError):
    """Exception raised when external media or object storage operations fail."""

    pass
