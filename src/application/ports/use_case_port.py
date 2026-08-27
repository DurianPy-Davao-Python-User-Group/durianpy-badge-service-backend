"""Base use case port contract."""

from abc import ABC, abstractmethod
from typing import Any


class UseCasePort(ABC):
    """Abstract boundary interface contract for application use cases."""

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """
        Execute the use case application logic.

        :param args: Positional arguments for use case execution.
        :param kwargs: Keyword arguments for use case execution.
        :returns: Result of use case execution.
        """
        pass
