"""Ingest configured Alpha Vantage daily history.

Run with: python -m app.commands.ingest_historical
"""

from __future__ import annotations

import argparse
import os

from ..database.connection import get_session, init_db
from ..marketdata.adapters.alphavantage import AlphaVantageAdapter
from ..marketdata.config import get_supported_symbols
from ..services.historical_ingestion import HistoricalIngestionCoordinator, summarize_results
from ..services.ingestion_service import IngestionService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest daily historical market data.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--symbol", help="Ingest one symbol")
    group.add_argument("--symbols", help="Comma-separated symbols")
    parser.add_argument(
        "--delay-seconds",
        type=float,
        default=float(os.getenv("HISTORICAL_INGESTION_DELAY_SECONDS", "1")),
        help="Delay between provider requests (default: 1)",
    )
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.delay_seconds < 0:
            raise ValueError("--delay-seconds must be non-negative")
        symbols = [args.symbol] if args.symbol else args.symbols.split(",") if args.symbols else None
        if symbols is not None:
            symbols = list(get_supported_symbols(",".join(symbols)))
        init_db()
        service = IngestionService(AlphaVantageAdapter())
        coordinator = HistoricalIngestionCoordinator(service, delay_seconds=args.delay_seconds)
        session_generator = get_session()
        session = next(session_generator)
        try:
            results = coordinator.ingest(session, symbols, args.start_date, args.end_date)
        finally:
            session_generator.close()
        for result in results:
            message = f"{result.symbol:<5} created={result.created:<4} skipped={result.skipped:<4} status={result.status}"
            if result.error:
                message += f" error={result.error}"
            print(message)
        summary = summarize_results(results)
        print("\nSummary:")
        print("successful={successful} failed={failed} no_data={no_data}".format(**summary))
        return 1 if summary["failed"] else 0
    except Exception as exc:
        print(f"ingest_historical failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
