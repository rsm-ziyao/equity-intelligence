# Phase 2D — Valuation Analysis

The valuation layer is descriptive research data, not investment advice.

## Current metric

Phase 2D calculates P/E at request time:

```text
current share price / latest annual diluted EPS
```

The denominator is always labeled with its fiscal basis, such as `FY2025
diluted EPS`. It is not labeled TTM. The service selects the newest annual
period with a reported diluted EPS. If the newest annual period omits EPS, an
older period may be used, and the actual fiscal year is exposed in the API.

Calculations use `Decimal` internally and return a two-decimal multiple.

P/E is unavailable when the quote is missing or stale, the annual EPS is
missing, EPS is zero, or EPS is negative. These conditions are returned as
explicit reasons rather than fabricated ratios.

## Quote freshness

The current quote is obtained through `QuoteService` and preserves its
provider, timestamps, market status, and freshness. `REALTIME`, `DELAYED`, and
`LATEST_TRADING_DAY` quotes may calculate P/E. A `STALE` quote remains visible
as market data but makes P/E unavailable with `STALE_MARKET_PRICE`. Delayed
data is never described as real-time.

## Deferred metrics

Price-to-sales and price-to-free-cash-flow are returned as unavailable. The
platform has company-level revenue and free cash flow, but does not yet have
shares outstanding or market capitalization. Dividing share price directly by
company-level revenue or free cash flow would be incorrect.

EV/revenue, EV/EBITDA, debt/equity, PEG, historical valuation ranges, peer
comparisons, and valuation verdicts are outside the Phase 2D scope.

No cheap, expensive, buy, sell, hold, fair-value, or intrinsic-value
classification is produced. A ratio without a validated comparison set is
descriptive only.

## Future requirements

Adding price-to-sales or price-to-free-cash-flow would require reliable shares
outstanding or market capitalization, plus validated TTM flow semantics.
These facts should be ingested with explicit provider provenance and period
semantics before those metrics are implemented.
