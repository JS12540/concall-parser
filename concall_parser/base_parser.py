from abc import ABC, abstractmethod


class BaseExtractor(ABC):
    """Base class for all extractors."""

    @abstractmethod
    def extract(self, *args, **kwargs):
        """Extracts data from the input."""
        pass
