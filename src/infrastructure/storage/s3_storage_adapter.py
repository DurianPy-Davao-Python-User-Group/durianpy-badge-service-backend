"""S3 storage infrastructure adapter."""

from typing import Any, Optional

import boto3
from botocore.exceptions import ClientError

from src.application.ports.storage.badge_storage_port import BadgeStoragePort
from src.core.settings import settings
from src.domain.exceptions.badge_design_exceptions import StoragePresignError


class S3StorageAdapter(BadgeStoragePort):
    """Infrastructure adapter managing object storage operations in AWS S3."""

    def __init__(
        self,
        s3_client: Optional[Any] = None,
        bucket_name: Optional[str] = None,
    ) -> None:
        """
        Initialize S3 storage adapter.

        :param s3_client: Optional boto3 S3 client; defaults to a client configured with settings.REGION.
        :type s3_client: Optional[Any]
        :param bucket_name: Optional S3 bucket name; defaults to settings.S3_BUCKET_NAME.
        :type bucket_name: Optional[str]
        """
        self.__s3_client = s3_client or boto3.client('s3', region_name=settings.REGION)
        self.__bucket_name = bucket_name if bucket_name is not None else settings.S3_BUCKET_NAME

    def generate_presigned_upload_url(
        self,
        storage_path: str,
        content_type: str,
        expires_in: Optional[int] = None,
    ) -> str:
        """
        Generate a pre-signed PUT upload URL for an asset in S3.

        :param storage_path: Object storage destination key or path.
        :type storage_path: str
        :param content_type: MIME type of the file to be uploaded.
        :type content_type: str
        :param expires_in: Expiration duration in seconds; defaults to settings.S3_PRESIGN_EXPIRATION_SECONDS.
        :type expires_in: Optional[int]
        :returns: Generated pre-signed PUT upload URL string.
        :rtype: str
        :raises StoragePresignError: If parameters are invalid or AWS S3 pre-signing fails.
        """
        if not storage_path or not isinstance(storage_path, str) or not storage_path.strip():
            raise StoragePresignError('Storage path must be a non-empty string.')

        if not content_type or not isinstance(content_type, str) or not content_type.strip():
            raise StoragePresignError('Content type must be a non-empty string.')

        if not self.__bucket_name:
            raise StoragePresignError('S3 bucket name is not configured.')

        expiration = expires_in if expires_in is not None else settings.S3_PRESIGN_EXPIRATION_SECONDS
        clean_path = storage_path.lstrip('/')

        try:
            url: str = self.__s3_client.generate_presigned_url(
                ClientMethod='put_object',
                Params={
                    'Bucket': self.__bucket_name,
                    'Key': clean_path,
                    'ContentType': content_type,
                },
                ExpiresIn=expiration,
            )
            return url
        except ClientError as exc:
            raise StoragePresignError(f'Failed to generate pre-signed upload URL: {exc}') from exc
