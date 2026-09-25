"""Use case port for generating badge artwork upload URLs."""

from abc import abstractmethod

from src.application.dtos.badge_design_dto import PresignUploadInputDTO, PresignUploadOutputDTO
from src.application.ports.use_case_port import UseCasePort


class GenerateBadgeDesignUploadUrlUseCasePort(UseCasePort):
    """Contract for generating an administrator's badge artwork upload URL."""

    @abstractmethod
    def execute(self, input_dto: PresignUploadInputDTO) -> PresignUploadOutputDTO:
        """Generate an upload URL for the validated artwork request.

        :param input_dto: Validated artwork upload request.
        :type input_dto: PresignUploadInputDTO
        :returns: Upload URL and relative storage path.
        :rtype: PresignUploadOutputDTO
        :raises StoragePresignError: If storage cannot generate an upload URL.
        """
        pass
