from abc import ABC, abstractmethod

from .models import Quote


class QuoteClient(ABC):
    provider_name: str

    @abstractmethod
    def get_quote(self, symbol: str) -> Quote:
        """Return one normalized current quote or raise a provider error."""
