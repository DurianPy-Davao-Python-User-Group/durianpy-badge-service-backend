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
    year_gt: Optional[str] = Query(
        None,
        description='Filter public badge designs after this ISO date (YYYY-MM-DD)',
        pattern=r'^\d{4}-\d{2}-\d{2}(T[^ ]+)?$',
    ),
    year_lt: Optional[str] = Query(
        None,
        description='Filter public badge designs before this ISO date (YYYY-MM-DD)',
        pattern=r'^\d{4}-\d{2}-\d{2}(T[^ ]+)?$',
    ),
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description='Number of items to return per page (default: 20, max: 100)',
    ),
    last_evaluated_key: Optional[str] = Query(
        None,
        alias='lastEvaluatedKey',
        description='Last evaluated key for pagination (used for fetching the next page)',
    ),
    use_case: GetPublicBadgeDesignsUseCasePort = Depends(get_public_badge_designs_use_case),
) -> PublicCatalogResponseSchema:
    """
    Handle GET /api/public/designs request to retrieve public badge designs.

    :param year: Optional year filter string (e.g., '2026').
    :type year: Optional[str]
    :param year_gt: Optional filter for designs after this ISO date (YYYY-MM-DD).
    :type year_gt: Optional[str]
    :param year_lt: Optional filter for designs before this ISO date (YYYY-MM-DD).
    :type year_lt: Optional[str]
    :param limit: Optional limit for number of items to return (default: 10).
    :type limit: int
    :param last_evaluated_key: Optional pagination key for fetching the next page.
    :type lastEvaluatedKey: Optional[str]
    :param use_case: Injected public badge designs discovery use case port.
    :type use_case: GetPublicBadgeDesignsUseCasePort
    :returns: Envelope containing list of public badge design items.
    :rtype: PublicCatalogResponseSchema
    """
    result = use_case.execute(
        year=year,
        year_gt=year_gt,
        year_lt=year_lt,
        limit=limit,
        last_evaluated_key=last_evaluated_key,
    )
    items = [PublicBadgeDesignItemSchema.model_validate(dto.model_dump()) for dto in result.data]
    return PublicCatalogResponseSchema(data=items, last_evaluated_key=result.last_evaluated_key)
