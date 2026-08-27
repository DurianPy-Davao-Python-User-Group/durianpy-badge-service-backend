"""CloudFront media URL resolver infrastructure adapter."""

from typing import Optional

from src.application.ports.storage.media_url_resolver_port import (
    MediaUrlResolverPort,
)
from src.core.settings import settings
from src.domain.exceptions.badge_design_exceptions import MediaResolutionError


class CloudFrontMediaUrlResolver(MediaUrlResolverPort):
    """Infrastructure adapter resolving storage paths via AWS CloudFront CDN."""

    def __init__(self, cdn_base_url: Optional[str] = None) -> None:
        """
        Initialize CloudFront URL resolver with base CDN URL.

        :param cdn_base_url: Optional base CDN URL; defaults to settings.CLOUDFRONT_URL.
        :type cdn_base_url: Optional[str]
        :param cdn_base_url: str
        """
        self.__cdn_base_url = (cdn_base_url or settings.CLOUDFRONT_URL).rstrip('/')

    def resolve_url(self, storage_path: str) -> str:
        """
        Resolve a storage path relative to the root of the bucket to a CloudFront URL.

        :param storage_path: Absolute path relative to the bucket root (e.g. 'designs/...').
        :type storage_path: str
        :returns: Fully qualified CloudFront CDN URL.
        :rtype: str
        :raises MediaResolutionError: If storage path is invalid or cannot be resolved.
        """
        if not storage_path or not isinstance(storage_path, str):
            raise MediaResolutionError('Storage path must be a non-empty string.')

        clean_path = storage_path.lstrip('/')
        return f'{self.__cdn_base_url}/{clean_path}'
