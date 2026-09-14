"""Unit tests for CognitoTokenVerifier adapter verifying RS256 tokens and claims."""

import time
from unittest.mock import MagicMock

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from src.domain.exceptions.auth_exceptions import AuthenticationError
from src.infrastructure.security.cognito_token_verifier import (
    CognitoTokenVerifier,
)


@pytest.fixture
def rsa_key_pair():
    """Generate RSA private and public key pair for RS256 token tests."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    return private_key, public_key


@pytest.fixture
def mock_jwks_client(rsa_key_pair):
    """Create a mock PyJWKClient returning the test public key."""
    _, public_key = rsa_key_pair
    mock_jwk = MagicMock()
    mock_jwk.key = public_key
    client = MagicMock(spec=jwt.PyJWKClient)
    client.get_signing_key_from_jwt.return_value = mock_jwk
    return client


def test_verify_valid_access_token(rsa_key_pair, mock_jwks_client) -> None:
    """Verify successfully decoding and mapping a valid Cognito access token."""
    private_key, _ = rsa_key_pair
    issuer = 'https://cognito-idp.ap-southeast-1.amazonaws.com/ap-southeast-1_test'
    payload = {
        'sub': 'user-uuid-1234',
        'username': 'Google_1029384756',
        'token_use': 'access',
        'iss': issuer,
        'client_id': 'app-client-id-xyz',
        'cognito:groups': ['google_1029384756'],
        'scope': 'openid email profile',
        'exp': int(time.time()) + 3600,
        'iat': int(time.time()),
    }
    token = jwt.encode(payload, private_key, algorithm='RS256', headers={'kid': 'key-1'})

    verifier = CognitoTokenVerifier(
        issuer=issuer,
        user_pool_id='ap-southeast-1_test',
        app_client_id='app-client-id-xyz',
        jwks_client=mock_jwks_client,
    )

    user = verifier.verify(token)

    assert user.user_id == 'user-uuid-1234'
    assert user.username == 'Google_1029384756'
    assert user.groups == ['google_1029384756']
    assert user.scopes == ['openid', 'email', 'profile']
    assert user.client_id == 'app-client-id-xyz'
    assert user.is_google_user is True
    assert user.is_regular_user is True
    assert user.is_admin is False


def test_verify_empty_or_non_string_token() -> None:
    """Verify AuthenticationError is raised when token is empty or not a string."""
    verifier = CognitoTokenVerifier(user_pool_id='pool', jwks_client=MagicMock())
    with pytest.raises(AuthenticationError, match='non-empty string'):
        verifier.verify('')

    with pytest.raises(AuthenticationError, match='non-empty string'):
        verifier.verify(None)  # type: ignore[arg-type]


def test_verify_unconfigured_jwks_client() -> None:
    """Verify AuthenticationError when JWKS client is unconfigured."""
    verifier = CognitoTokenVerifier(user_pool_id='', jwks_url='', jwks_client=None)
    with pytest.raises(AuthenticationError, match='misconfigured'):
        verifier.verify('some-token')


def test_verify_expired_token(rsa_key_pair, mock_jwks_client) -> None:
    """Verify AuthenticationError when token has expired."""
    private_key, _ = rsa_key_pair
    issuer = 'https://cognito-idp.ap-southeast-1.amazonaws.com/ap-southeast-1_test'
    payload = {
        'sub': 'user-uuid-1234',
        'token_use': 'access',
        'iss': issuer,
        'exp': int(time.time()) - 3600,
        'iat': int(time.time()) - 7200,
    }
    token = jwt.encode(payload, private_key, algorithm='RS256', headers={'kid': 'key-1'})

    verifier = CognitoTokenVerifier(
        issuer=issuer,
        user_pool_id='ap-southeast-1_test',
        jwks_client=mock_jwks_client,
    )

    with pytest.raises(AuthenticationError, match='Token has expired'):
        verifier.verify(token)


def test_verify_invalid_signature(rsa_key_pair, mock_jwks_client) -> None:
    """Verify AuthenticationError when token signature does not match key."""
    # Generate a different key to sign the token
    different_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    issuer = 'https://cognito-idp.ap-southeast-1.amazonaws.com/ap-southeast-1_test'
    payload = {
        'sub': 'user-uuid-1234',
        'token_use': 'access',
        'iss': issuer,
        'exp': int(time.time()) + 3600,
        'iat': int(time.time()),
    }
    token = jwt.encode(payload, different_private_key, algorithm='RS256', headers={'kid': 'key-1'})

    verifier = CognitoTokenVerifier(
        issuer=issuer,
        user_pool_id='ap-southeast-1_test',
        jwks_client=mock_jwks_client,
    )

    with pytest.raises(AuthenticationError, match='Invalid token signature'):
        verifier.verify(token)


def test_verify_invalid_issuer(rsa_key_pair, mock_jwks_client) -> None:
    """Verify AuthenticationError when issuer claim differs from expected."""
    private_key, _ = rsa_key_pair
    payload = {
        'sub': 'user-uuid-1234',
        'token_use': 'access',
        'iss': 'https://wrong-issuer.com',
        'exp': int(time.time()) + 3600,
        'iat': int(time.time()),
    }
    token = jwt.encode(payload, private_key, algorithm='RS256', headers={'kid': 'key-1'})

    verifier = CognitoTokenVerifier(
        issuer='https://expected-issuer.com',
        user_pool_id='ap-southeast-1_test',
        jwks_client=mock_jwks_client,
    )

    with pytest.raises(AuthenticationError, match='configured identity provider'):
        verifier.verify(token)


def test_verify_invalid_token_use(rsa_key_pair, mock_jwks_client) -> None:
    """Verify AuthenticationError when token_use is 'id' instead of 'access'."""
    private_key, _ = rsa_key_pair
    issuer = 'https://cognito-idp.ap-southeast-1.amazonaws.com/ap-southeast-1_test'
    payload = {
        'sub': 'user-uuid-1234',
        'token_use': 'id',
        'iss': issuer,
        'exp': int(time.time()) + 3600,
        'iat': int(time.time()),
    }
    token = jwt.encode(payload, private_key, algorithm='RS256', headers={'kid': 'key-1'})

    verifier = CognitoTokenVerifier(
        issuer=issuer,
        user_pool_id='ap-southeast-1_test',
        jwks_client=mock_jwks_client,
    )

    with pytest.raises(AuthenticationError, match="expected an 'access' token"):
        verifier.verify(token)


def test_verify_mismatched_client_id(rsa_key_pair, mock_jwks_client) -> None:
    """Verify AuthenticationError when client_id does not match configured app client."""
    private_key, _ = rsa_key_pair
    issuer = 'https://cognito-idp.ap-southeast-1.amazonaws.com/ap-southeast-1_test'
    payload = {
        'sub': 'user-uuid-1234',
        'token_use': 'access',
        'iss': issuer,
        'client_id': 'different-client',
        'exp': int(time.time()) + 3600,
        'iat': int(time.time()),
    }
    token = jwt.encode(payload, private_key, algorithm='RS256', headers={'kid': 'key-1'})

    verifier = CognitoTokenVerifier(
        issuer=issuer,
        user_pool_id='ap-southeast-1_test',
        app_client_id='expected-client',
        jwks_client=mock_jwks_client,
    )

    with pytest.raises(AuthenticationError, match='not issued for this client'):
        verifier.verify(token)


def test_verify_missing_sub_claim(rsa_key_pair, mock_jwks_client) -> None:
    """Verify AuthenticationError when token lacks 'sub' claim."""
    private_key, _ = rsa_key_pair
    issuer = 'https://cognito-idp.ap-southeast-1.amazonaws.com/ap-southeast-1_test'
    payload = {
        'token_use': 'access',
        'iss': issuer,
        'client_id': 'app-client-id-xyz',
        'exp': int(time.time()) + 3600,
        'iat': int(time.time()),
    }
    token = jwt.encode(payload, private_key, algorithm='RS256', headers={'kid': 'key-1'})

    verifier = CognitoTokenVerifier(
        issuer=issuer,
        user_pool_id='ap-southeast-1_test',
        app_client_id='app-client-id-xyz',
        jwks_client=mock_jwks_client,
    )

    with pytest.raises(AuthenticationError, match='missing required subject identifier'):
        verifier.verify(token)


def test_verify_jwks_client_fetch_error() -> None:
    """Verify AuthenticationError when PyJWKClient fails to fetch key from JWKS."""
    mock_client = MagicMock(spec=jwt.PyJWKClient)
    mock_client.get_signing_key_from_jwt.side_effect = jwt.PyJWKClientError('Network timeout')

    verifier = CognitoTokenVerifier(
        user_pool_id='ap-southeast-1_test',
        jwks_client=mock_client,
    )

    with pytest.raises(AuthenticationError, match='Unable to verify token signature'):
        verifier.verify('invalid.jwt.token')


def test_verify_malformed_token_header() -> None:
    """Verify AuthenticationError when JWT structure is unparseable."""
    mock_client = MagicMock(spec=jwt.PyJWKClient)
    mock_client.get_signing_key_from_jwt.side_effect = jwt.DecodeError('Invalid header padding')

    verifier = CognitoTokenVerifier(
        user_pool_id='ap-southeast-1_test',
        jwks_client=mock_client,
    )

    with pytest.raises(AuthenticationError, match='Invalid token format or header'):
        verifier.verify('bad-token')


def test_verify_corrupted_token_payload(mock_jwks_client) -> None:
    """Verify AuthenticationError on arbitrary decode failures."""
    mock_jwk = MagicMock()
    mock_jwk.key = 'dummy-key'
    mock_jwks_client.get_signing_key_from_jwt.return_value = mock_jwk

    verifier = CognitoTokenVerifier(
        user_pool_id='ap-southeast-1_test',
        jwks_client=mock_jwks_client,
    )

    with pytest.raises(AuthenticationError, match='Invalid or corrupted'):
        verifier.verify('corrupted.token.value')


def test_init_default_jwks_url_creation(monkeypatch) -> None:
    """Verify CognitoTokenVerifier initializes default PyJWKClient when jwks_url is resolved."""
    monkeypatch.setattr('src.core.settings.settings.COGNITO_USER_POOL_ID', 'test-pool-1')
    verifier = CognitoTokenVerifier()
    assert verifier._CognitoTokenVerifier__jwks_client is not None
