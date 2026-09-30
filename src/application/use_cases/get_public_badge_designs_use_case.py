"""Use case for discovering and retrieving public badge designs catalog."""

import base64
import binascii
import json
from datetime import datetime, timezone
from typing import Optional

from src.application.dtos.badge_design_dto import (
    PaginatedPublicCatalogOutputDTO,
    PublicBadgeDesignOutputDTO,
)
from src.application.ports.repositories.badge_design_repository import (
    BadgeDesignRepositoryPort,
)
from src.application.ports.storage.media_url_resolver_port import (
    MediaUrlResolverPort,
)
from src.application.ports.use_cases.get_public_badge_designs_use_case_port import (
    GetPublicBadgeDesignsUseCasePort,
)
from src.core.logging import log_execution
from src.domain.exceptions.base_exceptions import EntityValidationError


class GetPublicBadgeDesignsUseCase(GetPublicBadgeDesignsUseCasePort):
    """Use case interactor for public badge design catalog discovery."""

    def __init__(
        self,
        badge_design_repository: BadgeDesignRepositoryPort,
        media_url_resolver: MediaUrlResolverPort,
    ) -> None:
        """
        Initialize the use case with required repository and media resolver dependencies.

        :param badge_design_repository: Persistence repository port for badge designs.
        :type badge_design_repository: BadgeDesignRepositoryPort
        :param media_url_resolver: Port for resolving asset storage paths to public URLs.
        :type media_url_resolver: MediaUrlResolverPort
        """
        self.__repository = badge_design_repository
        self.__media_url_resolver = media_url_resolver

    @log_execution
    def execute(
        self,
        year: Optional[str] = None,
        year_gt: Optional[str] = None,
        year_lt: Optional[str] = None,
        limit: int = 10,
        last_evaluated_key: Optional[str] = None,
    ) -> PaginatedPublicCatalogOutputDTO:
        """
        Retrieve public badge design catalog items for a given year.

        :param year: Optional target catalog year. Defaults to current UTC year.
        :type year: Optional[str]
        :returns: A page of PublicBadgeDesignOutputDTO items with a continuation token.
        :rtype: PaginatedPublicCatalogOutputDTO
        """
        target_year = year or datetime.now(timezone.utc).strftime('%Y')
        decoded_key = self.__decode_cursor(last_evaluated_key)
        public_catalog_output = self.__repository.query_public_catalog(
            year=target_year,
            year_gt=year_gt,
            year_lt=year_lt,
            limit=limit,
            last_evaluated_key=decoded_key,
        )

        catalog_items: list[PublicBadgeDesignOutputDTO] = []
        for design in public_catalog_output.data:
            design_url = self.__media_url_resolver.resolve_url(design.storage_path)

            catalog_items.append(
                PublicBadgeDesignOutputDTO(
                    design_id=design.design_id,
                    meetup_name=design.meetup_detail.name,
                    meetup_date=design.meetup_detail.date,
                    venue=design.meetup_detail.venue,
                    name=design.name,
                    design_url=design_url,
                    role=design.role,
                )
            )

        return PaginatedPublicCatalogOutputDTO(
            data=catalog_items,
            last_evaluated_key=self.__encode_cursor(public_catalog_output.last_evaluated_key),
        )

    @staticmethod
    def __decode_cursor(cursor: Optional[str]) -> Optional[dict[str, object]]:
        """Decode a URL-safe catalog cursor into a DynamoDB key dictionary."""
        if cursor is None:
            return None
        try:
            padded_cursor = cursor + '=' * (-len(cursor) % 4)
            decoded = json.loads(base64.urlsafe_b64decode(padded_cursor.encode()).decode())
        except (ValueError, UnicodeDecodeError, binascii.Error) as exc:
            raise EntityValidationError(
                'Invalid lastEvaluatedKey pagination token.',
                code='REQUEST_VALIDATION_ERROR',
            ) from exc
        if not isinstance(decoded, dict):
            raise EntityValidationError('Invalid lastEvaluatedKey pagination token.', code='REQUEST_VALIDATION_ERROR')
        return decoded

    @staticmethod
    def __encode_cursor(cursor: Optional[dict[str, object]]) -> Optional[str]:
        """Encode a DynamoDB key dictionary as a URL-safe catalog cursor."""
        if cursor is None:
            return None
        payload = json.dumps(cursor, separators=(',', ':'), sort_keys=True).encode()
        return base64.urlsafe_b64encode(payload).decode().rstrip('=')
