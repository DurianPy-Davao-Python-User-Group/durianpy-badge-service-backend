"""Unit tests for S3StorageAdapter using Moto."""

from typing import Any
from unittest.mock import MagicMock, patch

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from src.domain.exceptions.badge_design_exceptions import StoragePresignError
from src.infrastructure.storage.s3_storage_adapter import S3StorageAdapter


@pytest.fixture
def mock_s3_bucket() -> str:
    """Fixture to supply a test bucket name."""
    return 'test-badge-bucket'


def test_init_defaults() -> None:
    """Test S3StorageAdapter initialization with default settings."""
    adapter = S3StorageAdapter()
    assert adapter is not None


def test_init_masks_client_error(caplog: pytest.LogCaptureFixture) -> None:
    """Translate client initialization failure without logging sensitive error text."""
    with patch('src.infrastructure.storage.s3_storage_adapter.boto3.client') as client_factory:
        client_factory.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'secret-token'}},
            'CreateClient',
        )
        with pytest.raises(StoragePresignError, match='Failed to initialize S3 client'):
            S3StorageAdapter(bucket_name='test-badge-bucket')

    assert 'secret-token' not in caplog.text


@mock_aws
def test_generate_presigned_upload_url_success(mock_s3_bucket: str) -> None:
    """Test generating a valid presigned PUT upload URL."""
    s3_client = boto3.client('s3', region_name='ap-southeast-1')
    s3_client.create_bucket(
        Bucket=mock_s3_bucket,
        CreateBucketConfiguration={'LocationConstraint': 'ap-southeast-1'},
    )

    adapter = S3StorageAdapter(s3_client=s3_client, bucket_name=mock_s3_bucket)
    url = adapter.generate_presigned_upload_url(
        storage_path='/designs/badge1.png',
        content_type='image/png',
        expires_in=1800,
    )

    assert isinstance(url, str)
    assert mock_s3_bucket in url
    assert 'designs/badge1.png' in url


@mock_aws
def test_generate_presigned_upload_url_default_expiration(mock_s3_bucket: str) -> None:
    """Test generating a presigned PUT upload URL using default expiration."""
    s3_client = boto3.client('s3', region_name='ap-southeast-1')
    s3_client.create_bucket(
        Bucket=mock_s3_bucket,
        CreateBucketConfiguration={'LocationConstraint': 'ap-southeast-1'},
    )

    adapter = S3StorageAdapter(s3_client=s3_client, bucket_name=mock_s3_bucket)
    url = adapter.generate_presigned_upload_url(
        storage_path='designs/badge2.png',
        content_type='image/png',
    )

    assert isinstance(url, str)
    assert 'designs/badge2.png' in url


def test_generate_presigned_upload_url_empty_path(mock_s3_bucket: str) -> None:
    """Test that empty or non-string storage path raises StoragePresignError."""
    adapter = S3StorageAdapter(bucket_name=mock_s3_bucket)
    none_value: Any = None

    with pytest.raises(StoragePresignError, match='Storage path must be a non-empty string.'):
        adapter.generate_presigned_upload_url(storage_path='', content_type='image/png')

    with pytest.raises(StoragePresignError, match='Storage path must be a non-empty string.'):
        adapter.generate_presigned_upload_url(storage_path=none_value, content_type='image/png')


def test_generate_presigned_upload_url_empty_content_type(mock_s3_bucket: str) -> None:
    """Test that empty or non-string content type raises StoragePresignError."""
    adapter = S3StorageAdapter(bucket_name=mock_s3_bucket)
    none_value: Any = None

    with pytest.raises(StoragePresignError, match='Content type must be a non-empty string.'):
        adapter.generate_presigned_upload_url(storage_path='path/to/file.png', content_type='')

    with pytest.raises(StoragePresignError, match='Content type must be a non-empty string.'):
        adapter.generate_presigned_upload_url(storage_path='path/to/file.png', content_type=none_value)


def test_generate_presigned_upload_url_missing_bucket() -> None:
    """Test that missing bucket name raises StoragePresignError."""
    adapter = S3StorageAdapter(bucket_name='')

    with pytest.raises(StoragePresignError, match='S3 bucket name is not configured.'):
        adapter.generate_presigned_upload_url(storage_path='path/to/file.png', content_type='image/png')


def test_generate_presigned_upload_url_client_error(mock_s3_bucket: str) -> None:
    """Test that ClientError from boto3 is translated into StoragePresignError."""
    mock_client = MagicMock()
    mock_client.generate_presigned_url.side_effect = ClientError(
        {'Error': {'Code': '500', 'Message': 'Internal Error'}},
        'generate_presigned_url',
    )

    adapter = S3StorageAdapter(s3_client=mock_client, bucket_name=mock_s3_bucket)

    with pytest.raises(StoragePresignError, match='Failed to generate pre-signed upload URL'):
        adapter.generate_presigned_upload_url(storage_path='designs/test.png', content_type='image/png')
