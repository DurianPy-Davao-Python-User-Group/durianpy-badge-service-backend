"""Tests for the admin badge artwork upload route."""

import re
from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from fastapi.testclient import TestClient

from src.application.ports.security.token_verifier_port import TokenVerifierPort
from src.domain.models.authenticated_user import AuthenticatedUser
from src.presentation.api.dependencies.auth_dependencies import get_token_verifier
from src.presentation.api.main import app

__VALID_REQUEST = {
    'meetupId': '9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d',
    'filename': 'badge_artwork.webp',
    'contentType': 'image/webp',
    'role': 'speaker',
}


@pytest.fixture
def verifier() -> Iterator[MagicMock]:
    """Provide an admin token verifier and restore the dependency override afterward."""
    mock_verifier = MagicMock(spec=TokenVerifierPort)
    mock_verifier.verify.return_value = AuthenticatedUser(
        user_id='sub-admin-1',
        username='admin_user',
        groups=['admin'],
    )
    app.dependency_overrides[get_token_verifier] = lambda: mock_verifier
    try:
        yield mock_verifier
    finally:
        app.dependency_overrides.pop(get_token_verifier, None)


def test_presign_requires_authentication() -> None:
    """Reject a presign request without an access token."""
    response = TestClient(app).post(
        '/api/admin/designs/presign',
        json=__VALID_REQUEST,
    )

    assert response.status_code == 401


def test_presign_returns_upload_url_and_canonical_storage_path(verifier: MagicMock) -> None:
    """Return a signed upload URL and a UTC storage path for an administrator."""
    with patch('src.infrastructure.storage.s3_storage_adapter.boto3.client') as client_factory:
        client_factory.return_value.generate_presigned_url.return_value = 'https://s3.example/upload'
        response = TestClient(app).post(
            '/api/admin/designs/presign',
            headers={'Authorization': 'Bearer test-admin-token'},
            json=__VALID_REQUEST,
        )

    assert response.status_code == 200
    assert response.json()['uploadUrl'] == 'https://s3.example/upload'
    assert re.fullmatch(
        r'designs/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d/speaker_\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z\.webp',
        response.json()['storagePath'],
    )


def test_presign_rejects_non_admin(verifier: MagicMock) -> None:
    """Reject an authenticated user outside the administrator groups."""
    verifier.verify.return_value = AuthenticatedUser(
        user_id='sub-attendee-1',
        username='attendee_user',
        groups=['attendee'],
    )
    response = TestClient(app).post(
        '/api/admin/designs/presign',
        headers={'Authorization': 'Bearer test-attendee-token'},
        json=__VALID_REQUEST,
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    ('field', 'value'),
    [
        ('meetupId', 'not-a-uuid'),
        ('filename', '../badge.png'),
        ('contentType', 'image/png'),
        ('role', 'organizer'),
    ],
)
def test_presign_rejects_invalid_request(field: str, value: str, verifier: MagicMock) -> None:
    """Reject invalid identifiers, filenames, content types, and roles."""
    with patch('src.infrastructure.storage.s3_storage_adapter.boto3.client'):
        response = TestClient(app).post(
            '/api/admin/designs/presign',
            headers={'Authorization': 'Bearer test-admin-token'},
            json={**__VALID_REQUEST, field: value},
        )

    assert response.status_code == 422
    assert response.json()['error']['code'] == 'REQUEST_VALIDATION_ERROR'


def test_presign_sanitizes_s3_failure(caplog: pytest.LogCaptureFixture, verifier: MagicMock) -> None:
    """Return a sanitized storage error when S3 cannot sign the request."""
    with patch('src.infrastructure.storage.s3_storage_adapter.boto3.client') as client_factory:
        client_factory.return_value.generate_presigned_url.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'secret-token'}},
            'PutObject',
        )
        response = TestClient(app).post(
            '/api/admin/designs/presign',
            headers={'Authorization': 'Bearer test-admin-token'},
            json=__VALID_REQUEST,
        )

    assert response.status_code == 500
    assert response.json()['error']['code'] == 'StoragePresignError'
    assert 'secret-token' not in response.text
    assert 'secret-token' not in caplog.text
