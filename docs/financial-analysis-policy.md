# Financial Analysis Policy

Phase 2C signals are deterministic research indicators derived from persisted
periodic financial statements. The thresholds below are initial product-policy
rules, not universal financial definitions and not investment advice.

## Growth

- `STRONG`: at least two valid growth metrics are at least +20%, and no core
  metric (revenue or net income) is below -10%.
- `MODERATE`: most valid metrics are positive, but the strong condition is not
  met. At least one positive metric must be meaningfully positive (initially
  +5%) rather than all metrics being effectively flat.
- `WEAK`: mixed or flat evidence without broad growth or broad decline.
- `DECLINING`: at least two valid metrics are below -10%, or both core metrics
  are below -10%.
- `UNAVAILABLE`: fewer than two valid comparable growth metrics exist.

Missing values are not negative evidence. Growth percentages are not computed
across zero denominators or sign changes.

## Profitability and margins

Margin movement is measured in percentage points. A 100 basis-point movement is
the initial materiality threshold. With four comparable periods, margin
analysis compares the latest two-period average with the preceding two-period
average. Otherwise it compares the latest period with the previous comparable
period. At least two of three margins must move consistently before a broad
classification is made.

Absolute margin levels do not determine trend status.

## Cash flow

Negative latest free cash flow takes precedence over trend direction. Same-sign
cash-flow changes use an initial 10% materiality threshold. Sign changes and
zero denominators use raw-value evidence instead of percentage growth.

## Financial strength

The indication uses only cash, total debt, operating cash flow, and free cash
flow. `HEALTHY` requires cash at least equal to total debt, positive operating
cash flow, and non-negative free cash flow. `WEAK` requires cash below total
debt and at least one negative cash-flow measure. This is not a liquidity or
solvency rating.

## Composite

Unavailable signals are ignored. `POSITIVE` requires at least three positive
signals and no more than one negative signal. `NEGATIVE` requires at least
three negative signals and no more than one positive signal. Fewer than two
available signals produces `UNAVAILABLE`; otherwise conflicting evidence is
`MIXED`.
