"""Tests for the admin badge artwork upload and badge design creation routes."""

import re
from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from fastapi.testclient import TestClient

from src.application.dtos.badge_design_dto import BadgeDesignOutputDTO, MeetupDetailDTO
from src.application.ports.security.token_verifier_port import TokenVerifierPort
from src.application.ports.use_cases.create_badge_design_use_case_port import CreateBadgeDesignUseCasePort
from src.domain.exceptions.badge_design_exceptions import (
    BadgeDesignCreationError,
    BadgeDesignVariantValidationError,
)
from src.domain.exceptions.techtix_exceptions import TechTixEventNotFoundError, TechTixGatewayError
from src.domain.models.authenticated_user import AuthenticatedUser
from src.presentation.api.dependencies.auth_dependencies import get_token_verifier
from src.presentation.api.dependencies.badge_design_dependencies import get_create_badge_design_use_case
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


# ---------------------------------------------------------------------------
# POST /api/admin/designs — create badge design
# ---------------------------------------------------------------------------

__MEETUP_ID = '9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d'

__VALID_SPEAKER_CREATE_REQUEST = {
    'meetupId': __MEETUP_ID,
    'name': 'PyCon Davao 2026 – Speaker',
    'storagePath': f'designs/{__MEETUP_ID}/speaker_2026-10-07T00-00-00Z.webp',
    'role': 'speaker',
    'speakers': [{'name': 'Jane Doe', 'talkTitle': 'Intro to Python', 'email': 'jane@example.com'}],
}

__VALID_PARTICIPANT_CREATE_REQUEST = {
    'meetupId': __MEETUP_ID,
    'name': 'PyCon Davao 2026 – Participant',
    'storagePath': f'designs/{__MEETUP_ID}/participant_2026-10-07T00-00-00Z.webp',
    'role': 'participant',
}


@pytest.fixture
def create_use_case() -> Iterator[MagicMock]:
    """Provide a mock CreateBadgeDesignUseCasePort and clean up DI override afterward."""
    mock_uc = MagicMock(spec=CreateBadgeDesignUseCasePort)
    app.dependency_overrides[get_create_badge_design_use_case] = lambda: mock_uc
    try:
        yield mock_uc
    finally:
        app.dependency_overrides.pop(get_create_badge_design_use_case, None)


def _make_output_dto(
    *,
    role: str,
    speakers: list[dict] | None = None,
) -> BadgeDesignOutputDTO:
    """Build a minimal BadgeDesignOutputDTO for stubbing the use case."""
    return BadgeDesignOutputDTO(
        design_id='d-test-001',
        name='Test Badge',
        storage_path=f'designs/{__MEETUP_ID}/{role}.webp',
        role=role,
        meetup_detail=MeetupDetailDTO(meetup_id=__MEETUP_ID, name='PyCon Davao 2026'),
        speakers=speakers,
    )


def test_create_badge_design_requires_authentication(create_use_case: MagicMock) -> None:
    """Reject a create-design request that carries no access token."""
    response = TestClient(app).post('/api/admin/designs', json=__VALID_SPEAKER_CREATE_REQUEST)

    assert response.status_code == 401
    create_use_case.execute.assert_not_called()


def test_create_badge_design_rejects_non_admin(
    verifier: MagicMock,
    create_use_case: MagicMock,
) -> None:
    """Reject an authenticated attendee attempting to create a badge design."""
    verifier.verify.return_value = AuthenticatedUser(
        user_id='sub-attendee-2',
        username='attendee_user',
        groups=['attendee'],
    )
    response = TestClient(app).post(
        '/api/admin/designs',
        headers={'Authorization': 'Bearer attendee-token'},
        json=__VALID_SPEAKER_CREATE_REQUEST,
    )

    assert response.status_code == 403
    create_use_case.execute.assert_not_called()


def test_create_speaker_badge_design_returns_201(
    verifier: MagicMock,
    create_use_case: MagicMock,
) -> None:
    """Return HTTP 201 with the persisted speaker badge design representation."""
    create_use_case.execute.return_value = _make_output_dto(
        role='speaker',
        speakers=[{'name': 'Jane Doe', 'talk_title': 'Intro to Python', 'email': 'jane@example.com'}],
    )

    response = TestClient(app).post(
        '/api/admin/designs',
        headers={'Authorization': 'Bearer admin-token'},
        json=__VALID_SPEAKER_CREATE_REQUEST,
    )

    assert response.status_code == 201
    body = response.json()
    assert body['designId'] == 'd-test-001'
    assert body['meetupId'] == __MEETUP_ID
    assert body['role'] == 'speaker'
    assert body['speakers'] is not None
    assert len(body['speakers']) == 1
    assert body['speakers'][0]['name'] == 'Jane Doe'
    create_use_case.execute.assert_called_once()


def test_create_participant_badge_design_returns_201_without_speakers(
    verifier: MagicMock,
    create_use_case: MagicMock,
) -> None:
    """Return HTTP 201 for a participant badge design; speakers must be absent."""
    create_use_case.execute.return_value = _make_output_dto(role='participant', speakers=None)

    response = TestClient(app).post(
        '/api/admin/designs',
        headers={'Authorization': 'Bearer admin-token'},
        json=__VALID_PARTICIPANT_CREATE_REQUEST,
    )

    assert response.status_code == 201
    body = response.json()
    assert body['role'] == 'participant'
    assert body['speakers'] is None


def test_create_badge_design_participant_with_speakers_returns_422(
    verifier: MagicMock,
    create_use_case: MagicMock,
) -> None:
    """Return 422 when a participant badge design carries speaker data (domain invariant)."""
    create_use_case.execute.side_effect = BadgeDesignVariantValidationError(
        "Badge design 'd-x' with role 'participant' must not include speaker data."
    )

    response = TestClient(app).post(
        '/api/admin/designs',
        headers={'Authorization': 'Bearer admin-token'},
        json={**__VALID_PARTICIPANT_CREATE_REQUEST, 'speakers': [{'name': 'Jane Doe'}]},
    )

    assert response.status_code == 422
    assert response.json()['error']['code'] == 'BadgeDesignVariantValidationError'


def test_create_badge_design_speaker_without_speakers_returns_422(
    verifier: MagicMock,
    create_use_case: MagicMock,
) -> None:
    """Return 422 when a speaker badge design is missing its speakers list (domain invariant)."""
    create_use_case.execute.side_effect = BadgeDesignVariantValidationError(
        "Badge design 'd-x' with role 'speaker' must include at least one speaker."
    )

    response = TestClient(app).post(
        '/api/admin/designs',
        headers={'Authorization': 'Bearer admin-token'},
        json={k: v for k, v in __VALID_SPEAKER_CREATE_REQUEST.items() if k != 'speakers'},
    )

    assert response.status_code == 422
    assert response.json()['error']['code'] == 'BadgeDesignVariantValidationError'


def test_create_badge_design_meetup_not_found_returns_404(
    verifier: MagicMock,
    create_use_case: MagicMock,
) -> None:
    """Return 404 when the referenced meetup does not exist in TechTix."""
    create_use_case.execute.side_effect = TechTixEventNotFoundError(f'Event with entryId {__MEETUP_ID} does not exist.')

    response = TestClient(app).post(
        '/api/admin/designs',
        headers={'Authorization': 'Bearer admin-token'},
        json=__VALID_SPEAKER_CREATE_REQUEST,
    )

    assert response.status_code == 404
    assert response.json()['error']['code'] == 'TechTixEventNotFoundError'


def test_create_badge_design_gateway_error_returns_400(
    verifier: MagicMock,
    create_use_case: MagicMock,
) -> None:
    """Return 400 when TechTix gateway returns an unexpected error."""
    create_use_case.execute.side_effect = TechTixGatewayError(
        f'TechTix request for meetup {__MEETUP_ID} failed: connection refused'
    )

    response = TestClient(app).post(
        '/api/admin/designs',
        headers={'Authorization': 'Bearer admin-token'},
        json=__VALID_SPEAKER_CREATE_REQUEST,
    )

    assert response.status_code == 400
    assert response.json()['error']['code'] == 'TechTixGatewayError'


def test_create_badge_design_persistence_failure_returns_500(
    caplog: pytest.LogCaptureFixture,
    verifier: MagicMock,
    create_use_case: MagicMock,
) -> None:
    """Return 500 and suppress internal details when DynamoDB persistence fails."""
    create_use_case.execute.side_effect = BadgeDesignCreationError('DynamoDB TransactWrite failed: secret-db-arn')

    response = TestClient(app).post(
        '/api/admin/designs',
        headers={'Authorization': 'Bearer admin-token'},
        json=__VALID_SPEAKER_CREATE_REQUEST,
    )

    assert response.status_code == 500
    assert response.json()['error']['code'] == 'BadgeDesignCreationError'
    assert 'secret-db-arn' not in response.text


@pytest.mark.parametrize(
    ('field', 'value'),
    [
        ('meetupId', 'not-a-uuid'),
        ('name', ''),
        ('storagePath', ''),
        ('role', 'organizer'),
    ],
)
def test_create_badge_design_rejects_invalid_request_fields(
    field: str,
    value: str,
    verifier: MagicMock,
    create_use_case: MagicMock,
) -> None:
    """Return 422 for malformed meetup IDs, blank names/paths, and unknown roles."""
    response = TestClient(app).post(
        '/api/admin/designs',
        headers={'Authorization': 'Bearer admin-token'},
        json={**__VALID_SPEAKER_CREATE_REQUEST, field: value},
    )

    assert response.status_code == 422
    assert response.json()['error']['code'] == 'REQUEST_VALIDATION_ERROR'
    create_use_case.execute.assert_not_called()
