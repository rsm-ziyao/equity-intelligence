from dataclasses import dataclass
from threading import Lock
from time import monotonic

from .models import Quote


@dataclass
class CacheEntry:
    quote: Quote
    stored_at: float


class QuoteCache:
    def __init__(self, ttl_seconds: int = 45, stale_seconds: int = 600):
        self.ttl_seconds = ttl_seconds
        self.stale_seconds = stale_seconds
        self._entries: dict[str, CacheEntry] = {}
        self._locks: dict[str, Lock] = {}
        self._global_lock = Lock()

    def get(self, symbol: str) -> tuple[Quote | None, bool]:
        entry = self._entries.get(symbol)
        if not entry:
            return None, False
        age = monotonic() - entry.stored_at
        if age <= self.ttl_seconds:
            return entry.quote, True
        if age <= self.stale_seconds:
            return entry.quote, False
        return None, False

    def put(self, symbol: str, quote: Quote) -> None:
        self._entries[symbol] = CacheEntry(quote=quote, stored_at=monotonic())

    def symbol_lock(self, symbol: str) -> Lock:
        with self._global_lock:
            return self._locks.setdefault(symbol, Lock())
