"""Unit tests for CloudFrontMediaUrlResolver infrastructure adapter."""

import pytest

from src.domain.exceptions.badge_design_exceptions import MediaResolutionError
from src.infrastructure.storage.cloudfront_media_url_resolver import (
    CloudFrontMediaUrlResolver,
)


def test_cloudfront_media_url_resolver_resolves_path() -> None:
    """Verify resolver formats storage path relative to root of bucket into CDN URL."""
    resolver = CloudFrontMediaUrlResolver(cdn_base_url='https://cdn.example.com')
    url = resolver.resolve_url('designs/abc/badge.webp')
    assert url == 'https://cdn.example.com/designs/abc/badge.webp'


def test_cloudfront_media_url_resolver_handles_slashes() -> None:
    """Verify resolver normalizes leading/trailing slashes."""
    resolver = CloudFrontMediaUrlResolver(cdn_base_url='https://cdn.example.com/')
    url = resolver.resolve_url('/designs/abc/badge.webp')
    assert url == 'https://cdn.example.com/designs/abc/badge.webp'


def test_cloudfront_media_url_resolver_raises_domain_exception_on_invalid_path() -> None:
    """Verify resolver raises MediaResolutionError on empty or invalid storage path."""
    resolver = CloudFrontMediaUrlResolver(cdn_base_url='https://cdn.example.com')
    with pytest.raises(MediaResolutionError) as exc_info:
        resolver.resolve_url('')
    assert 'Storage path must be a non-empty string' in str(exc_info.value)
