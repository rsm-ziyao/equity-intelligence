class MarketDataError(Exception):
    pass


class ValidationError(MarketDataError):
    pass


class ProviderRateLimitError(MarketDataError):
    pass


class ProviderError(MarketDataError):
    pass
