"""Abstract port contract for resolving media and asset public URLs."""

from abc import ABC, abstractmethod


class MediaUrlResolverPort(ABC):
    """Abstract port for resolving storage paths to accessible public URLs."""

    @abstractmethod
    def resolve_url(self, storage_path: str) -> str:
        """
        Resolve a relative bucket storage path to a full public URL.

        :param storage_path: Absolute path relative to the root of the storage bucket.
        :type storage_path: str
        :returns: Fully qualified public URL string.
        :rtype: str
        """
        pass
