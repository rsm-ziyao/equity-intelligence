from .cache import QuoteCache
from .client import QuoteClient
from .models import Freshness, QuoteResult, normalize_symbol


class QuoteService:
    def __init__(self, client: QuoteClient, cache: QuoteCache | None = None):
        self.client = client
        self.cache = cache or QuoteCache()

    def get_quote(self, symbol: str) -> QuoteResult:
        normalized = normalize_symbol(symbol)
        cached, fresh = self.cache.get(normalized)
        if cached and fresh:
            return QuoteResult(symbol=normalized, quote=cached, freshness=cached.freshness)
        with self.cache.symbol_lock(normalized):
            cached, fresh = self.cache.get(normalized)
            if cached and fresh:
                return QuoteResult(symbol=normalized, quote=cached, freshness=cached.freshness)
            try:
                quote = self.client.get_quote(normalized)
                self.cache.put(normalized, quote)
                return QuoteResult(symbol=normalized, quote=quote, freshness=quote.freshness)
            except Exception as exc:
                if cached:
                    stale = cached.model_copy(update={"freshness": Freshness.STALE})
                    return QuoteResult(symbol=normalized, quote=stale, error="Live quote unavailable; serving cached stale data.", freshness=Freshness.STALE)
                return QuoteResult(symbol=normalized, error=str(exc), freshness=Freshness.UNAVAILABLE)

    def get_quotes(self, symbols: list[str]) -> tuple[list[QuoteResult], list[str]]:
        normalized = list(dict.fromkeys(normalize_symbol(symbol) for symbol in symbols))
        results = [self.get_quote(symbol) for symbol in normalized]
        return results, [result.symbol for result in results if result.quote is None]
