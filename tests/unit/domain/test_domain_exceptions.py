"""Unit tests for domain exceptions."""

from src.domain.exceptions.badge_design_exceptions import (
    BadgeDesignCreationError,
    BadgeDesignNotFoundError,
    BadgeDesignQueryError,
    BadgeDesignRepositoryError,
    MediaResolutionError,
)
from src.domain.exceptions.base_exceptions import (
    DomainError,
    EntityNotFoundError,
    RepositoryError,
    StorageServiceError,
)


def test_domain_exception_hierarchy() -> None:
    """Verify domain exception inheritance relationships and properties."""
    assert issubclass(EntityNotFoundError, DomainError)
    assert issubclass(RepositoryError, DomainError)
    assert issubclass(StorageServiceError, DomainError)

    assert issubclass(BadgeDesignNotFoundError, EntityNotFoundError)
    assert issubclass(BadgeDesignRepositoryError, RepositoryError)
    assert issubclass(BadgeDesignCreationError, BadgeDesignRepositoryError)
    assert issubclass(BadgeDesignQueryError, BadgeDesignRepositoryError)
    assert issubclass(MediaResolutionError, StorageServiceError)

    err = BadgeDesignCreationError('Persistence failed')
    assert err.message == 'Persistence failed'
    assert err.code == 'BadgeDesignCreationError'
