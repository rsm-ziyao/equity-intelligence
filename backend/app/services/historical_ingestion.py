"""Sequential multi-symbol orchestration for daily historical ingestion."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Callable, Iterable

from sqlalchemy.orm import Session

from ..marketdata.exceptions import ProviderRateLimitError
from ..marketdata.config import get_supported_symbols
from .ingestion_service import IngestionService


@dataclass(frozen=True)
class SymbolIngestionResult:
    symbol: str
    status: str
    created: int = 0
    skipped: int = 0
    error: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


class HistoricalIngestionCoordinator:
    """Run the existing single-symbol daily ingestion path sequentially."""

    def __init__(
        self,
        ingestion_service: IngestionService,
        delay_seconds: float = 0.0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if delay_seconds < 0:
            raise ValueError("delay_seconds must be non-negative")
        self.ingestion_service = ingestion_service
        self.delay_seconds = delay_seconds
        self.sleep = sleep

    def ingest(
        self,
        session: Session,
        symbols: Iterable[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[SymbolIngestionResult]:
        if isinstance(symbols, str):
            symbol_value = symbols
        elif symbols is not None:
            symbol_value = ",".join(symbols)
        else:
            symbol_value = None
        selected = get_supported_symbols(symbol_value)
        results: list[SymbolIngestionResult] = []
        rate_limited = False

        for index, symbol in enumerate(selected):
            if rate_limited:
                results.append(SymbolIngestionResult(
                    symbol=symbol,
                    status="not_attempted",
                    error="Not attempted after provider rate limit",
                ))
                continue

            if index and self.delay_seconds:
                self.sleep(self.delay_seconds)

            try:
                stats = self.ingestion_service.ingest_daily(
                    session, symbol, start_date=start_date, end_date=end_date
                )
                status = "no_data" if stats.get("no_data") else "ok"
                results.append(SymbolIngestionResult(
                    symbol=symbol,
                    status=status,
                    created=stats["created"],
                    skipped=stats["skipped"],
                ))
            except Exception as exc:
                cause = exc
                while getattr(cause, "__cause__", None) is not None:
                    cause = cause.__cause__
                is_rate_limited = isinstance(cause, ProviderRateLimitError)
                results.append(SymbolIngestionResult(
                    symbol=symbol,
                    status="rate_limited" if is_rate_limited else "failed",
                    error=str(cause),
                ))
                if is_rate_limited:
                    rate_limited = True

        return results


def summarize_results(results: Iterable[SymbolIngestionResult]) -> dict[str, int]:
    summary = {"successful": 0, "failed": 0, "no_data": 0}
    for result in results:
        if result.status in {"ok", "not_attempted"}:
            summary["successful"] += 1 if result.status == "ok" else 0
        elif result.status == "no_data":
            summary["no_data"] += 1
        else:
            summary["failed"] += 1
    return summary
