"""Tests for generating badge artwork upload URLs."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.application.dtos.badge_design_dto import PresignUploadInputDTO
from src.application.ports.storage.badge_storage_port import BadgeStoragePort
from src.application.use_cases.generate_badge_design_upload_url_use_case import (
    GenerateBadgeDesignUploadUrlUseCase,
)


def test_generate_upload_url_uses_utc_storage_path() -> None:
    """Sign a canonical relative path with the requested content type."""
    storage = MagicMock(spec=BadgeStoragePort)
    storage.generate_presigned_upload_url.return_value = 'https://s3.example/upload'
    request = PresignUploadInputDTO(
        meetup_id='9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d',
        filename='badge_artwork.webp',
        content_type='image/webp',
        role='speaker',
    )

    with patch('src.application.use_cases.generate_badge_design_upload_url_use_case.datetime') as clock:
        clock.now.return_value = datetime(2026, 9, 12, 10, 40, tzinfo=timezone.utc)
        response = GenerateBadgeDesignUploadUrlUseCase(storage).execute(request)

    assert response.upload_url == 'https://s3.example/upload'
    assert response.storage_path == 'designs/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d/speaker_2026-09-12T10-40-00Z.webp'
    storage.generate_presigned_upload_url.assert_called_once_with(
        storage_path='designs/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d/speaker_2026-09-12T10-40-00Z.webp',
        content_type='image/webp',
    )
    clock.now.assert_called_once_with(timezone.utc)
