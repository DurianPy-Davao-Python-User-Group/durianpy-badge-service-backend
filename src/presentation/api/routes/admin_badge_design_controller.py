"""Administrative badge design API routes."""

from fastapi import APIRouter, Depends, status

from src.application.dtos.badge_design_dto import PresignUploadInputDTO
from src.application.ports.use_cases.generate_badge_design_upload_url_use_case_port import (
    GenerateBadgeDesignUploadUrlUseCasePort,
)
from src.domain.models.authenticated_user import AuthenticatedUser
from src.presentation.api.dependencies.auth_dependencies import require_admin
from src.presentation.api.dependencies.badge_design_dependencies import (
    get_generate_badge_design_upload_url_use_case,
)
from src.presentation.api.schemas.admin_badge_design_schema import (
    PresignBadgeDesignUploadRequestSchema,
    PresignBadgeDesignUploadResponseSchema,
)

router = APIRouter(prefix='/api/admin/designs', tags=['Admin Badge Designs'])


@router.post(
    '/presign',
    response_model=PresignBadgeDesignUploadResponseSchema,
    status_code=status.HTTP_200_OK,
)
def presign_badge_design_upload(
    request: PresignBadgeDesignUploadRequestSchema,
    current_user: AuthenticatedUser = Depends(require_admin),
    use_case: GenerateBadgeDesignUploadUrlUseCasePort = Depends(get_generate_badge_design_upload_url_use_case),
) -> PresignBadgeDesignUploadResponseSchema:
    """Generate an administrator's signed badge artwork upload URL.

    :param request: Validated artwork upload request.
    :type request: PresignBadgeDesignUploadRequestSchema
    :param current_user: Authenticated administrator.
    :type current_user: AuthenticatedUser
    :param use_case: Injected upload URL generation use case.
    :type use_case: GenerateBadgeDesignUploadUrlUseCasePort
    :returns: Signed upload URL and relative storage path.
    :rtype: PresignBadgeDesignUploadResponseSchema
    """
    output = use_case.execute(
        PresignUploadInputDTO(
            meetup_id=str(request.meetup_id),
            filename=request.filename,
            content_type=request.content_type,
            role=request.role,
        )
    )
    return PresignBadgeDesignUploadResponseSchema.model_validate(output.model_dump())
