"""Port abstraction for the external TechTix gateway."""

from abc import ABC, abstractmethod

from src.application.dtos.badge_design_dto import MeetupDetailDTO


class TechTixGatewayPort(ABC):
    """Outbound port interface for interacting with the external TechTix service."""

    @abstractmethod
    def get_meetup_details(self, meetup_id: str) -> MeetupDetailDTO:
        """
        Retrieve verified meetup details from TechTix by event ID.

        :param meetup_id: The unique identifier (entryId) of the TechTix event.
        :type meetup_id: str
        :returns: Essential meetup details mapped to a DTO.
        :rtype: MeetupDetailDTO
        :raises TechTixEventNotFoundError: If the event does not exist (404).
        :raises TechTixGatewayError: If communication with the gateway fails.
        """
        pass
