import os
import re
from pathlib import Path

from dotenv import load_dotenv


# Local development uses the repository-level .env. `override=False` keeps
# explicitly supplied process environment variables authoritative.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env", override=False)


ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")
ALPHAVANTAGE_BASE = os.getenv("ALPHAVANTAGE_BASE", "https://www.alphavantage.co")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
FINNHUB_BASE = os.getenv("FINNHUB_BASE", "https://finnhub.io/api/v1")
FINNHUB_REALTIME_ENTITLED = os.getenv("FINNHUB_REALTIME_ENTITLED", "false").lower() in {"1", "true", "yes", "on"}

DEFAULT_SUPPORTED_SYMBOLS = (
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL",
    "META", "TSLA", "AVGO", "AMD", "NFLX",
)
SUPPORTED_SYMBOLS_ENV = "SUPPORTED_SYMBOLS"
SYMBOL_PATTERN = re.compile(r"^[A-Z][A-Z0-9.-]{0,9}$")


def get_supported_symbols(value: str | None = None) -> tuple[str, ...]:
    """Return the normalized, validated historical-ingestion universe."""
    raw = value if value is not None else os.getenv(SUPPORTED_SYMBOLS_ENV)
    symbols = raw.split(",") if raw is not None else list(DEFAULT_SUPPORTED_SYMBOLS)

    normalized: list[str] = []
    seen: set[str] = set()
    for raw_symbol in symbols:
        symbol = raw_symbol.strip().upper()
        if not symbol:
            continue
        if not SYMBOL_PATTERN.fullmatch(symbol):
            raise ValueError(f"Invalid stock symbol: {raw_symbol.strip()!r}")
        if symbol not in seen:
            normalized.append(symbol)
            seen.add(symbol)

    if not normalized:
        raise ValueError("SUPPORTED_SYMBOLS must contain at least one symbol")
    return tuple(normalized)
