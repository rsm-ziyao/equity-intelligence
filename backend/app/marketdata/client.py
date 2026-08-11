from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterable
from .models import Bar


class MarketDataClient(ABC):
    """Provider-agnostic market data interface.

    Implementations must return lists/iterables of canonical `Bar` records.
    """

    @abstractmethod
    def get_intraday(self, symbol: str, interval: str = "1min") -> Iterable[Bar]:
        """Return latest available intraday bars for `symbol`.

        interval: e.g. '1min', '5min'
        """

    @abstractmethod
    def get_historical_daily(self, symbol: str, start: str | None = None, end: str | None = None) -> Iterable[Bar]:
        """Return historical daily bars for `symbol` between optional start/end dates (ISO strings).
        """
