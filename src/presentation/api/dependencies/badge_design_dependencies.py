"""Dependency injection providers for badge design repository, resolvers, and use cases."""

from fastapi import Depends

from src.application.ports.repositories.badge_design_repository import (
    BadgeDesignRepositoryPort,
)
from src.application.ports.storage.badge_storage_port import BadgeStoragePort
from src.application.ports.storage.media_url_resolver_port import (
    MediaUrlResolverPort,
)
from src.application.ports.use_cases.generate_badge_design_upload_url_use_case_port import (
    GenerateBadgeDesignUploadUrlUseCasePort,
)
from src.application.ports.use_cases.get_public_badge_designs_use_case_port import (
    GetPublicBadgeDesignsUseCasePort,
)
from src.application.use_cases.generate_badge_design_upload_url_use_case import (
    GenerateBadgeDesignUploadUrlUseCase,
)
from src.application.use_cases.get_public_badge_designs_use_case import (
    GetPublicBadgeDesignsUseCase,
)
from src.infrastructure.db.pynamo_repositories.pynamo_badge_design_repository import (
    PynamoBadgeDesignRepository,
)
from src.infrastructure.storage.cloudfront_media_url_resolver import (
    CloudFrontMediaUrlResolver,
)
from src.infrastructure.storage.s3_storage_adapter import S3StorageAdapter


def get_badge_design_repository() -> BadgeDesignRepositoryPort:
    """
    Provide concrete BadgeDesignRepositoryPort implementation.

    :returns: Instance of PynamoBadgeDesignRepository.
    :rtype: BadgeDesignRepositoryPort
    """
    return PynamoBadgeDesignRepository()


def get_media_url_resolver() -> MediaUrlResolverPort:
    """
    Provide concrete MediaUrlResolverPort implementation.

    :returns: Instance of CloudFrontMediaUrlResolver.
    :rtype: MediaUrlResolverPort
    """
    return CloudFrontMediaUrlResolver()


def get_badge_storage_port() -> BadgeStoragePort:
    """Provide the badge artwork storage adapter.

    :returns: S3 badge artwork storage adapter.
    :rtype: BadgeStoragePort
    :raises StoragePresignError: If the S3 client cannot be initialized.
    """
    return S3StorageAdapter()


def get_generate_badge_design_upload_url_use_case(
    badge_storage: BadgeStoragePort = Depends(get_badge_storage_port),
) -> GenerateBadgeDesignUploadUrlUseCasePort:
    """Provide the badge artwork upload URL use case.

    :param badge_storage: Injected badge artwork storage port.
    :type badge_storage: BadgeStoragePort
    :returns: Configured badge artwork upload URL use case.
    :rtype: GenerateBadgeDesignUploadUrlUseCasePort
    """
    return GenerateBadgeDesignUploadUrlUseCase(badge_storage=badge_storage)


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
