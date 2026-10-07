"""Administrative badge design API routes."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status

from src.application.dtos.badge_design_dto import CreateBadgeDesignInputDTO, MeetupDetailDTO, PresignUploadInputDTO
from src.application.ports.use_cases.create_badge_design_use_case_port import CreateBadgeDesignUseCasePort
from src.application.ports.use_cases.generate_badge_design_upload_url_use_case_port import (
    GenerateBadgeDesignUploadUrlUseCasePort,
)
from src.domain.models.authenticated_user import AuthenticatedUser
from src.presentation.api.dependencies.auth_dependencies import require_admin
from src.presentation.api.dependencies.badge_design_dependencies import (
    get_create_badge_design_use_case,
    get_generate_badge_design_upload_url_use_case,
)
from src.presentation.api.schemas.admin_badge_design_schema import (
    CreateBadgeDesignRequestSchema,
    CreateBadgeDesignResponseSchema,
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


@router.post(
    '',
    response_model=CreateBadgeDesignResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary='Create Badge Design',
    description='Create and persist a new badge design blueprint. Meetup details are verified against TechTix.',
)
def create_badge_design(
    request: CreateBadgeDesignRequestSchema,
    current_user: AuthenticatedUser = Depends(require_admin),
    use_case: CreateBadgeDesignUseCasePort = Depends(get_create_badge_design_use_case),
) -> CreateBadgeDesignResponseSchema:
    """Handle POST /api/admin/designs to create a new badge design blueprint.

    Delegates all orchestration — TechTix meetup resolution, domain validation,
    DynamoDB persistence, and CloudFront URL resolution — to the use case layer.
    The authenticated user's ``user_id`` is forwarded as the audit ``created_by`` value.
    ``year`` and ``iso_date`` are derived from the UTC wall-clock at request time and
    are used as DynamoDB GSI keys; they are not accepted from the client.

    :param request: Validated badge design creation request body.
    :type request: CreateBadgeDesignRequestSchema
    :param current_user: Authenticated administrator injected by ``require_admin``.
    :type current_user: AuthenticatedUser
    :param use_case: Injected badge design creation use case port.
    :type use_case: CreateBadgeDesignUseCasePort
    :returns: HTTP 201 response containing the persisted badge design representation.
    :rtype: CreateBadgeDesignResponseSchema
    :raises TechTixEventNotFoundError: Propagated as 404 when the meetup does not exist in TechTix.
    :raises BadgeDesignVariantValidationError: Propagated as 422 on role-specific invariant violations.
    :raises BadgeDesignCreationError: Propagated as 500 on persistence failure.
    """
    now_utc = datetime.now(timezone.utc)
    year = now_utc.strftime('%Y')
    iso_date = now_utc.strftime('%Y-%m-%d')

    input_dto = CreateBadgeDesignInputDTO(
        name=request.name,
        storage_path=request.storage_path,
        role=request.role,
        year=year,
        iso_date=iso_date,
        created_by=current_user.user_id,
        meetup_detail=MeetupDetailDTO(meetup_id=str(request.meetup_id)),
        speakers=[speaker.to_dict() for speaker in request.speakers] if request.speakers else None,
    )

    output = use_case.execute(input_dto)

    return CreateBadgeDesignResponseSchema.model_validate(output.model_dump())
