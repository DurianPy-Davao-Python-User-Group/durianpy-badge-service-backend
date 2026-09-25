"""Use case for generating badge artwork upload URLs."""

from datetime import datetime, timezone

from src.application.dtos.badge_design_dto import PresignUploadInputDTO, PresignUploadOutputDTO
from src.application.ports.storage.badge_storage_port import BadgeStoragePort
from src.application.ports.use_cases.generate_badge_design_upload_url_use_case_port import (
    GenerateBadgeDesignUploadUrlUseCasePort,
)
from src.core.logging import log_execution


class GenerateBadgeDesignUploadUrlUseCase(GenerateBadgeDesignUploadUrlUseCasePort):
    """Create the canonical artwork path and request its upload URL."""

    def __init__(self, badge_storage: BadgeStoragePort) -> None:
        """Store the badge artwork storage port.

        :param badge_storage: Storage port that signs upload requests.
        :type badge_storage: BadgeStoragePort
        """
        self.__badge_storage = badge_storage

    @log_execution
    def execute(self, input_dto: PresignUploadInputDTO) -> PresignUploadOutputDTO:
        """Generate an upload URL for a badge artwork file.

        :param input_dto: Validated artwork upload request.
        :type input_dto: PresignUploadInputDTO
        :returns: Signed upload URL and canonical relative storage path.
        :rtype: PresignUploadOutputDTO
        :raises StoragePresignError: If storage cannot generate an upload URL.
        """
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M-%SZ')
        storage_path = f'designs/{input_dto.meetup_id}/{input_dto.role}_{timestamp}.webp'
        upload_url = self.__badge_storage.generate_presigned_upload_url(
            storage_path=storage_path,
            content_type=input_dto.content_type,
        )
        return PresignUploadOutputDTO(upload_url=upload_url, storage_path=storage_path)
