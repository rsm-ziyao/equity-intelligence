"""Ingest Alpha Vantage quarterly and annual company fundamentals."""
from __future__ import annotations
import argparse, os, time
from datetime import datetime
from ..database.connection import get_session, init_db
from ..database.models import Stock
from ..fundamentals.adapters.alphavantage import AlphaVantageFundamentalsAdapter
from ..fundamentals.exceptions import FundamentalsRateLimitError
from ..fundamentals.normalize import normalize_rows
from ..marketdata.config import get_supported_symbols
from ..repositories.fundamentals_repository import FundamentalsRepository
from ..repositories.stock_repository import StockRepository

def build_parser():
    parser = argparse.ArgumentParser(description="Ingest company fundamentals from Alpha Vantage.")
    group = parser.add_mutually_exclusive_group(); group.add_argument("--symbol"); group.add_argument("--symbols")
    parser.add_argument("--delay-seconds", type=float, default=float(os.getenv("FUNDAMENTALS_INGESTION_DELAY_SECONDS", "1")))
    return parser

def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.delay_seconds < 0: print("--delay-seconds must be non-negative"); return 1
    try: symbols = get_supported_symbols(args.symbol or args.symbols)
    except ValueError as exc: print(exc); return 1
    try: client = AlphaVantageFundamentalsAdapter()
    except Exception as exc: print(f"ingest_fundamentals failed: {exc}"); return 1
    init_db(); generator = get_session(); session = next(generator); totals = {"created":0,"updated":0,"skipped":0,"unavailable":0,"errors":0}; rate_limited = False
    try:
        for index, symbol in enumerate(symbols):
            if rate_limited: break
            if index and args.delay_seconds: time.sleep(args.delay_seconds)
            try:
                stock = StockRepository.get_or_create(session, symbol)
                retrieved = datetime.utcnow()
                income = normalize_rows(client.get_income_statement(symbol), symbol, client.provider_name, "income", retrieved)
                if args.delay_seconds: time.sleep(args.delay_seconds)
                balance = normalize_rows(client.get_balance_sheet(symbol), symbol, client.provider_name, "balance", retrieved)
                if args.delay_seconds: time.sleep(args.delay_seconds)
                cash = normalize_rows(client.get_cash_flow(symbol), symbol, client.provider_name, "cash_flow", retrieved)
                if not income and not balance and not cash: totals["unavailable"] += 1; print(f"{symbol:<5} unavailable"); continue
                stats = FundamentalsRepository.upsert_records(session, stock.id, income, cash, balance)
                for key in ("created", "updated"): totals[key] += stats[key]
                print(f"{symbol:<5} created={stats['created']} updated={stats['updated']} skipped={stats['skipped']} status=ok")
            except FundamentalsRateLimitError as exc:
                totals["errors"] += 1; rate_limited = True; print(f"{symbol:<5} status=rate_limited error={exc}")
            except Exception as exc:
                session.rollback(); totals["errors"] += 1; print(f"{symbol:<5} status=error error={exc}")
    finally: generator.close()
    if rate_limited:
        print("Stopped after provider rate limit; remaining symbols were not attempted.")
    print("\nSummary:"); print(" ".join(f"{key}={value}" for key, value in totals.items()))
    return 1 if totals["errors"] else 0
if __name__ == "__main__": raise SystemExit(main())
