"""Use case for creating a new badge design blueprint."""

import uuid

from src.application.dtos.badge_design_dto import BadgeDesignOutputDTO, CreateBadgeDesignInputDTO, MeetupDetailDTO
from src.application.ports.gateways.techtix_gateway_port import TechTixGatewayPort
from src.application.ports.repositories.badge_design_repository import BadgeDesignRepositoryPort
from src.application.ports.storage.media_url_resolver_port import MediaUrlResolverPort
from src.application.ports.use_cases.create_badge_design_use_case_port import CreateBadgeDesignUseCasePort
from src.core.logging import log_execution, logger, mask_string
from src.domain.models.badge_design import BadgeDesignDomainModel, BadgeRole
from src.domain.models.meetup_detail import MeetupDetailDomainModel


class CreateBadgeDesignUseCase(CreateBadgeDesignUseCasePort):
    """Use case interactor for creating and persisting a new badge design blueprint.

    Orchestrates TechTix meetup resolution, domain entity construction and validation,
    DynamoDB snapshot persistence, and CloudFront URL resolution.
    """

    def __init__(
        self,
        badge_design_repository: BadgeDesignRepositoryPort,
        media_url_resolver: MediaUrlResolverPort,
        techtix_gateway: TechTixGatewayPort,
    ) -> None:
        """Initialise the use case with its required outbound port dependencies.

        :param badge_design_repository: Persistence repository port for badge designs.
        :type badge_design_repository: BadgeDesignRepositoryPort
        :param media_url_resolver: Port for resolving storage paths to public CloudFront URLs.
        :type media_url_resolver: MediaUrlResolverPort
        :param techtix_gateway: Outbound gateway port for verifying meetup details via TechTix.
        :type techtix_gateway: TechTixGatewayPort
        """
        self.__repository = badge_design_repository
        self.__media_url_resolver = media_url_resolver
        self.__techtix_gateway = techtix_gateway

    @log_execution
    def execute(self, input_dto: CreateBadgeDesignInputDTO) -> BadgeDesignOutputDTO:
        """Create, validate, persist, and return a new badge design blueprint.

        Execution steps:

        1. Resolve verified meetup details from TechTix using the ``meetup_id``
           supplied in *input_dto* (overrides any client-supplied meetup metadata).
        2. Construct a ``BadgeDesignDomainModel`` and trigger role-specific domain
           invariant validation (speaker / participant rules).
        3. Persist the domain entity snapshot to DynamoDB via the repository port.
        4. Resolve the canonical CloudFront URL for the stored artwork.
        5. Map the persisted entity to ``BadgeDesignOutputDTO`` and return.

        :param input_dto: Validated input data for the new badge design.
        :type input_dto: CreateBadgeDesignInputDTO
        :returns: Output DTO representing the persisted badge design with resolved URL.
        :rtype: BadgeDesignOutputDTO
        :raises TechTixEventNotFoundError: If the meetup does not exist in TechTix.
        :raises TechTixGatewayError: If communication with TechTix fails.
        :raises BadgeDesignVariantValidationError: If role-specific domain invariants are violated.
        :raises BadgeDesignCreationError: If persisting the badge design to the repository fails.
        """
        meetup_id = input_dto.meetup_detail.meetup_id

        # Step 1 — Resolve verified meetup details from TechTix.
        logger.info("Resolving TechTix meetup details for meetup '%s'.", meetup_id)
        meetup_detail_dto: MeetupDetailDTO = self.__techtix_gateway.get_meetup_details(meetup_id)

        # Step 2 — Construct and domain-validate the badge design entity.
        design_id = str(uuid.uuid4())
        domain_meetup_detail = MeetupDetailDomainModel(
            meetup_id=meetup_detail_dto.meetup_id,
            name=meetup_detail_dto.name,
            date=meetup_detail_dto.date,
            venue=meetup_detail_dto.venue,
        )
        design = BadgeDesignDomainModel(
            design_id=design_id,
            name=input_dto.name,
            storage_path=input_dto.storage_path,
            role=BadgeRole(input_dto.role),
            speakers=input_dto.speakers,
            meetup_detail=domain_meetup_detail,
        )

        logger.info(
            "Created badge design '%s' for meetup '%s' by user '%s'.",
            design.design_id,
            meetup_id,
            mask_string(input_dto.created_by),
        )

        # Step 3 — Persist the validated domain entity snapshot to DynamoDB.
        persisted_design: BadgeDesignDomainModel = self.__repository.create_design(
            design=design,
            year=input_dto.year,
            iso_date=input_dto.iso_date,
            created_by=input_dto.created_by,
        )

        # Step 4 — Resolve the CloudFront URL for the persisted artwork.
        design_url = self.__media_url_resolver.resolve_url(persisted_design.storage_path)

        logger.info(
            "Persisted badge design '%s' for meetup '%s'; resolved URL '%s'.",
            persisted_design.design_id,
            meetup_id,
            design_url,
        )

        # Step 5 — Map to output DTO.
        return self.__to_output_dto(persisted_design, design_url)

    @staticmethod
    def __to_output_dto(design: BadgeDesignDomainModel, design_url: str) -> BadgeDesignOutputDTO:
        """Map a persisted domain entity to its output DTO representation.

        :param design: The persisted badge design domain entity.
        :type design: BadgeDesignDomainModel
        :param design_url: Fully qualified CloudFront URL for the design artwork.
        :type design_url: str
        :returns: Serialisable output DTO.
        :rtype: BadgeDesignOutputDTO
        """
        return BadgeDesignOutputDTO(
            design_id=design.design_id,
            name=design.name,
            storage_path=design_url,
            role=design.role,
            meetup_detail=MeetupDetailDTO(
                meetup_id=design.meetup_detail.meetup_id,
                name=design.meetup_detail.name,
                date=design.meetup_detail.date,
                venue=design.meetup_detail.venue,
            ),
            speakers=design.speakers,
        )
