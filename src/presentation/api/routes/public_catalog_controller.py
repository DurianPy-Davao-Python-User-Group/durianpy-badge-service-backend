"""Public catalog discovery API route controller."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from src.application.ports.use_cases.get_public_badge_designs_use_case_port import (
    GetPublicBadgeDesignsUseCasePort,
)
from src.presentation.api.dependencies.badge_design_dependencies import (
    get_public_badge_designs_use_case,
)
from src.presentation.api.schemas.public_catalog_schema import (
    PublicBadgeDesignItemSchema,
    PublicCatalogResponseSchema,
)

router = APIRouter(prefix='/api/public', tags=['Public Catalog'])


@router.get(
    '/designs',
    response_model=PublicCatalogResponseSchema,
    status_code=status.HTTP_200_OK,
    summary='Public Catalog Discovery',
    description='Discover and list public badge designs available in the catalog.',
)
def get_public_badge_designs(
    year: Optional[str] = Query(
        None,
        description='Filter public badge designs by catalog year (e.g. 2026)',
        pattern=r'^\d{4}$',
    ),
    use_case: GetPublicBadgeDesignsUseCasePort = Depends(get_public_badge_designs_use_case),
    # TODO: Query params gt and lt year
    # year_gt: Optional[str] = Query(None, description='Filter designs after this ISO date'),
    # year_lt: Optional[str] = Query(None, description='Filter designs before this ISO date'),
    # TODO: Pagination
    # page: int = Query(1, ge=1, description='Page number'),
    # limit: int = Query(20, ge=1, le=100, description='Page item limit'),
) -> PublicCatalogResponseSchema:
    """
    Handle GET /api/public/designs request to retrieve public badge designs.

    :param year: Optional year filter string (e.g., '2026').
    :type year: Optional[str]
    :param use_case: Injected public badge designs discovery use case port.
    :type use_case: GetPublicBadgeDesignsUseCasePort
    :returns: Envelope containing list of public badge design items.
    :rtype: PublicCatalogResponseSchema
    """
    dtos = use_case.execute(year=year)
    items = [PublicBadgeDesignItemSchema.model_validate(dto.model_dump()) for dto in dtos]
    return PublicCatalogResponseSchema(data=items)
