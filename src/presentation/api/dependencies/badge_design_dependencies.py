"""Dependency injection providers for badge design repository, resolvers, and use cases."""

from fastapi import Depends

from src.application.ports.repositories.badge_design_repository import (
    BadgeDesignRepositoryPort,
)
from src.application.ports.storage.media_url_resolver_port import (
    MediaUrlResolverPort,
)
from src.application.ports.use_cases.get_public_badge_designs_use_case_port import (
    GetPublicBadgeDesignsUseCasePort,
)
from src.application.use_cases.get_public_badge_designs_use_case import (
    GetPublicBadgeDesignsUseCase,
)
from src.infrastructure.db.mock_dynamodb import ensure_mock_database
from src.infrastructure.db.pynamo_repositories.pynamo_badge_design_repository import (
    PynamoBadgeDesignRepository,
)
from src.infrastructure.storage.cloudfront_media_url_resolver import (
    CloudFrontMediaUrlResolver,
)


def get_badge_design_repository() -> BadgeDesignRepositoryPort:
    """
    Provide concrete BadgeDesignRepositoryPort implementation.

    Initializes mock DynamoDB storage if table is not yet provisioned.

    :returns: Instance of PynamoBadgeDesignRepository.
    :rtype: BadgeDesignRepositoryPort
    """
    ensure_mock_database()
    return PynamoBadgeDesignRepository()


def get_media_url_resolver() -> MediaUrlResolverPort:
    """
    Provide concrete MediaUrlResolverPort implementation.

    :returns: Instance of CloudFrontMediaUrlResolver.
    :rtype: MediaUrlResolverPort
    """
    return CloudFrontMediaUrlResolver()


def get_public_badge_designs_use_case(
    repository: BadgeDesignRepositoryPort = Depends(get_badge_design_repository),
    media_url_resolver: MediaUrlResolverPort = Depends(get_media_url_resolver),
) -> GetPublicBadgeDesignsUseCasePort:
    """
    Provide GetPublicBadgeDesignsUseCase instance with injected dependencies.

    :param repository: Injected badge design repository port.
    :type repository: BadgeDesignRepositoryPort
    :param media_url_resolver: Injected media URL resolver port.
    :type media_url_resolver: MediaUrlResolverPort
    :returns: Configured use case interactor instance implementing GetPublicBadgeDesignsUseCasePort.
    :rtype: GetPublicBadgeDesignsUseCasePort
    """
    return GetPublicBadgeDesignsUseCase(
        badge_design_repository=repository,
        media_url_resolver=media_url_resolver,
    )
