"""PynamoDB implementation of badge design repository port."""

from typing import Optional

from pynamodb.exceptions import PynamoDBException
from pynamodb.transactions import TransactGet, TransactWrite

from src.application.ports.repositories.badge_design_repository import (
    BadgeDesignRepositoryPort,
)
from src.domain.exceptions.badge_design_exceptions import (
    BadgeDesignCreationError,
    BadgeDesignQueryError,
)
from src.domain.models.badge_design import BadgeDesignDomainModel
from src.domain.models.meetup_detail import MeetupDetailDomainModel
from src.infrastructure.db.models.badge_design import BadgeDesign


class PynamoBadgeDesignRepository(BadgeDesignRepositoryPort):
    """PynamoDB repository for badge design persistence operations."""

    __MEETUP_PK_PREFIX = 'MEETUP#'
    __BADGE_DESIGN_SK_PREFIX = 'BADGEDESIGN#'
    __YEAR_GSI1PK_PREFIX = 'YEAR#'
    __MEETUPDATE_GSI1SK_PREFIX = 'MEETUPDATE#'

    def __build_keys(
        self,
        meetup_id: str,
        design_id: str,
        year: str,
        iso_date: str,
    ) -> tuple[str, str, str, str]:
        """
        Format primary keys (pk, sk) and GSI1 keys (gsi1pk, gsi1sk) with key prefixes.

        :param meetup_id: Meetup identifier.
        :param design_id: Badge design identifier.
        :param year: Catalog year string.
        :param iso_date: ISO formatted date string.
        :returns: Tuple of (pk, sk, gsi1pk, gsi1sk).
        """
        pk = f'{self.__MEETUP_PK_PREFIX}{meetup_id}'
        sk = f'{self.__BADGE_DESIGN_SK_PREFIX}{design_id}'
        gsi1pk = f'{self.__YEAR_GSI1PK_PREFIX}{year}'
        gsi1sk = f'{self.__MEETUPDATE_GSI1SK_PREFIX}{iso_date}'
        return pk, sk, gsi1pk, gsi1sk

    def __to_domain(self, record: BadgeDesign) -> BadgeDesignDomainModel:
        """
        Map a BadgeDesign PynamoDB record to a BadgeDesignDomainModel.

        :param record: BadgeDesign database item record.
        :type record: BadgeDesign
        :returns: Converted domain entity.
        :rtype: BadgeDesignDomainModel
        """
        return BadgeDesignDomainModel(
            design_id=record.design_id,
            name=record.name,
            storage_path=record.storage_path,
            role=record.role,
            speakers=record.speakers,
            meetup_detail=MeetupDetailDomainModel(
                meetup_id=record.meetup_id,
                name=record.meetup_name,
                date=record.meetup_date,
                venue=record.venue,
            ),
        )

    def create_design(
        self,
        design: BadgeDesignDomainModel,
        year: str,
        iso_date: str,
        created_by: str,
    ) -> BadgeDesignDomainModel:
        """
        Persist a new badge design blueprint item in DynamoDB using a transaction.

        :param design: Badge design domain entity.
        :type design: BadgeDesignDomainModel
        :param year: Target catalog year.
        :type year: str
        :param iso_date: Target ISO date for sorting.
        :type iso_date: str
        :param created_by: Creator identifier for audit attribution.
        :type created_by: str
        :returns: Persisted BadgeDesignDomainModel instance.
        :rtype: BadgeDesignDomainModel
        :raises BadgeDesignCreationError: If DynamoDB persistence operation fails.
        """
        try:
            pk, sk, gsi1pk, gsi1sk = self.__build_keys(
                meetup_id=design.meetup_detail.meetup_id,
                design_id=design.design_id,
                year=year,
                iso_date=iso_date,
            )

            record = BadgeDesign(
                pk=pk,
                sk=sk,
                gsi1pk=gsi1pk,
                gsi1sk=gsi1sk,
                design_id=design.design_id,
                meetup_id=design.meetup_detail.meetup_id,
                name=design.name,
                storage_path=design.storage_path,
                role=design.role,
                speakers=design.speakers,
                meetup_name=design.meetup_detail.name,
                meetup_date=design.meetup_detail.date,
                venue=design.meetup_detail.venue,
                durianpy_created_by=created_by,
            )

            connection = BadgeDesign._get_connection().connection
            with TransactWrite(connection=connection) as transaction:
                transaction.save(record)

            return self.__to_domain(record)
        except PynamoDBException as exc:
            raise BadgeDesignCreationError(f'Failed to persist badge design in DynamoDB: {exc}') from exc
        except Exception as exc:
            if isinstance(exc, BadgeDesignCreationError):
                raise
            raise BadgeDesignCreationError(f'Unexpected error creating badge design: {exc}') from exc

    def query_public_catalog(
        self,
        year: str,
        year_gt: Optional[str] = None,
        year_lt: Optional[str] = None,
    ) -> list[BadgeDesignDomainModel]:
        """
        Query public catalog badge designs for a given year with date filters.

        Uses DynamoDB transactions (TransactGet) on the base table to guarantee
        ACID read consistency after resolving matching partition and sort keys from GSI1.

        :param year: Target catalog year (YYYY).
        :type year: str
        :param year_gt: Optional lower bound ISO date filter.
        :type year_gt: Optional[str]
        :param year_lt: Optional upper bound ISO date filter.
        :type year_lt: Optional[str]
        :returns: List of matching BadgeDesignDomainModel instances.
        :rtype: list[BadgeDesignDomainModel]
        :raises BadgeDesignQueryError: If DynamoDB query or transaction operation fails.
        """
        try:
            gsi1pk = f'{self.__YEAR_GSI1PK_PREFIX}{year}'

            range_key_condition = None
            if year_gt is not None and year_lt is not None:
                range_key_condition = BadgeDesign.gsi1sk.between(
                    f'{self.__MEETUPDATE_GSI1SK_PREFIX}{year_gt}',
                    f'{self.__MEETUPDATE_GSI1SK_PREFIX}{year_lt}',
                )
            elif year_gt is not None:
                range_key_condition = BadgeDesign.gsi1sk > f'{self.__MEETUPDATE_GSI1SK_PREFIX}{year_gt}'
            elif year_lt is not None:
                range_key_condition = BadgeDesign.gsi1sk < f'{self.__MEETUPDATE_GSI1SK_PREFIX}{year_lt}'

            query_results = list(
                BadgeDesign.query_by_year_index.query(
                    gsi1pk,
                    range_key_condition=range_key_condition,
                )
            )

            if not query_results:
                return []

            # TODO: Implement chunking for query results exceeding DynamoDB's 100-item
            # transaction limit
            connection = BadgeDesign._get_connection().connection
            with TransactGet(connection=connection) as transaction:
                actions = [transaction.get(BadgeDesign, hash_key=item.pk, range_key=item.sk) for item in query_results]

            records = [getattr(action, 'value', None) or item for action, item in zip(actions, query_results)]

            return [self.__to_domain(record) for record in records]
        except PynamoDBException as exc:
            raise BadgeDesignQueryError(f'Failed to query public catalog from DynamoDB: {exc}') from exc
        except Exception as exc:
            if isinstance(exc, BadgeDesignQueryError):
                raise
            raise BadgeDesignQueryError(f'Unexpected error querying public catalog: {exc}') from exc
