"""Abstract port contract for badge asset storage operations."""

from abc import ABC, abstractmethod


class BadgeStoragePort(ABC):
    """Abstract port defining object storage interactions for badge assets."""

    @abstractmethod
    def generate_presigned_upload_url(
        self,
        storage_path: str,
        content_type: str,
        expires_in: int = 3600,
    ) -> str:
        """
        Generate a pre-signed PUT upload URL for an asset.

        :param storage_path: Object storage destination key or path.
        :type storage_path: str
        :param content_type: MIME type of the file to be uploaded.
        :type content_type: str
        :param expires_in: Expiration duration in seconds, defaults to 3600.
        :type expires_in: int
        :returns: Generated pre-signed upload URL string.
        :rtype: str
        :raises StoragePresignError: When pre-signed URL generation fails.
        """
        pass
