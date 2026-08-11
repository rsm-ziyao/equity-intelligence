# Database Schema

## Overview

Equity Intelligence uses PostgreSQL to persist market data indexed and validated from various providers.

The schema is optimized for:
- **Fast time-series queries** (date range filters, latest price lookups)
- **Duplicate prevention** (same provider + timestamp = unique per stock)
- **Multi-provider support** (allow same timestamp from different sources for future comparison)
- **Referential integrity** (cascading deletes, foreign key constraints)

## Tables

### `stocks`

Master registry of stocks. Tracks company metadata.

**Columns:**
| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO INCREMENT | Unique stock identifier |
| `symbol` | VARCHAR(10) | UNIQUE, NOT NULL, INDEX | Stock ticker (e.g., "AAPL", "MSFT") |
| `company_name` | VARCHAR(255) | NULL | Company full name (optional, can be enriched) |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Record insertion time |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last modification time |

**Indexes:**
- `PK stocks(id)` — Primary key
- `UQ stocks(symbol)` — Unique stock ticker (prevents duplicate symbols)
- `IDX stocks(symbol)` — Fast lookup by symbol

**Example:**
```sql
INSERT INTO stocks (symbol, company_name) VALUES ('AAPL', 'Apple Inc.');
-- id=1, symbol='AAPL', company_name='Apple Inc.', created_at=NOW(), updated_at=NOW()
```

---

### `stock_prices`

Time-series price data (OHLCV: Open, High, Low, Close, Volume).

Supports:
- Intraday data (multiple bars per day at different intervals: 1min, 5min, 15min, etc.)
- Daily data (one bar per trading day, adjusted for splits/dividends)
- Multi-provider data (Alpha Vantage, Polygon, FRED, etc.)

**Columns:**
| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO INCREMENT | Unique price record identifier |
| `stock_id` | INTEGER | FOREIGN KEY (stocks.id), ON DELETE CASCADE, INDEX | Reference to stock master record |
| `timestamp` | TIMESTAMP | NOT NULL, INDEX | ISO timestamp of the price bar (supports both intraday and daily) |
| `open` | DOUBLE PRECISION | NOT NULL | Opening price in USD |
| `high` | DOUBLE PRECISION | NOT NULL | Highest price in USD |
| `low` | DOUBLE PRECISION | NOT NULL | Lowest price in USD |
| `close` | DOUBLE PRECISION | NOT NULL | Closing price in USD |
| `volume` | INTEGER | NOT NULL | Number of shares traded |
| `provider` | VARCHAR(50) | NOT NULL | Data provider identifier (e.g., "alpha_vantage", "polygon_io") |
| `provider_timestamp` | VARCHAR(50) | NOT NULL | Raw timestamp string from provider (for debugging provider-specific formats) |
| `retrieved_at` | TIMESTAMP | NOT NULL | When we fetched this data from the provider |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | When we inserted into our database |

**Indexes:**
- `PK stock_prices(id)` — Primary key
- `FK stock_prices(stock_id)` → `stocks(id)` with ON DELETE CASCADE
- `UQ stock_prices(stock_id, provider, provider_timestamp)` — Uniqueness constraint
- `IDX stock_prices(stock_id, timestamp)` — Fast date-range queries
- `IDX stock_prices(stock_id)` — Fast lookup by stock
- `IDX stock_prices(timestamp)` — Fast lookup by date

**Uniqueness Constraint (Duplicate Prevention):**
```sql
UNIQUE (stock_id, provider, provider_timestamp)
```

Why this works:
- ✅ **Same provider + same timestamp = rejected** → Prevents duplicate ingestion
- ✅ **Different provider + same timestamp = allowed** → Enables cross-provider comparison
- ✅ **Same provider + different timestamp = allowed** → Enables intraday updates

**Example:**
```sql
INSERT INTO stock_prices (stock_id, timestamp, open, high, low, close, volume, provider, provider_timestamp, retrieved_at)
VALUES (1, '2026-08-11 14:30:00', 150.0, 151.5, 149.5, 151.0, 1000000, 'alpha_vantage', '2026-08-11 14:30:00', '2026-08-11 14:35:00');
```

---

## Relationships

### Foreign Key: stock_prices.stock_id → stocks.id

- **Type:** Many-to-one (one stock can have many prices)
- **Delete Policy:** CASCADE (deleting a stock cascades to all its price records)
- **Constraint:** Every price record must reference a valid stock

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Alpha Vantage API                                          │
│  (or other provider)                                         │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  MarketDataClient.get_intraday() / get_historical_daily()  │
│  (Provider-agnostic interface)                              │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  Bar (Canonical dataclass)                                  │
│  - Timestamp parsing                                        │
│  - Numeric validation (prices >= 0)                         │
│  - Relational validation (high >= max(OHLC))                │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  IngestionService                                           │
│  - Ensures Stock exists (create if needed)                  │
│  - Checks for duplicate (stock_id, provider, timestamp)     │
│  - Inserts or skips StockPrice record                       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  PostgreSQL                                                 │
│  - stocks table (1 AAPL record)                             │
│  - stock_prices table (1000s of price records)              │
└─────────────────────────────────────────────────────────────┘
```

---

## Initialization

### Starting PostgreSQL via Docker Compose

```bash
# From repository root
docker-compose up postgres
```

This starts PostgreSQL 16 with:
- User: `equityuser`
- Password: `equitypass`
- Database: `equitydb`
- Port: 5432

Wait for log message: `database system is ready to accept connections`

### Creating Tables

Tables are created automatically on first application startup:

```python
from app.database.connection import init_db

# Call once at startup (idempotent)
init_db()
```

Or via management script:

```bash
cd backend
python3 -c "from app.database.connection import init_db; init_db(); print('Database initialized')"
```

### Verifying Schema

Connect to PostgreSQL:

```bash
docker-compose exec postgres psql -U equityuser -d equitydb
```

List tables:

```sql
\dt
```

Inspect stocks table:

```sql
\d stocks
```

Inspect stock_prices table:

```sql
\d stock_prices
```

---

## Querying

### Get latest price for a stock

```sql
SELECT * FROM stock_prices 
WHERE stock_id = 1 
ORDER BY timestamp DESC 
LIMIT 1;
```

### Get price range for a date range

```sql
SELECT * FROM stock_prices 
WHERE stock_id = 1 
  AND timestamp >= '2026-08-01' 
  AND timestamp <= '2026-08-31' 
ORDER BY timestamp ASC;
```

### Get prices from multiple providers for comparison

```sql
SELECT provider, timestamp, close 
FROM stock_prices 
WHERE stock_id = 1 
  AND timestamp = '2026-08-11 14:30:00' 
ORDER BY provider;
```

### Check for duplicates (should be empty)

```sql
SELECT stock_id, provider, provider_timestamp, COUNT(*) 
FROM stock_prices 
GROUP BY stock_id, provider, provider_timestamp 
HAVING COUNT(*) > 1;
```

---

## Environment Variables

Set in `.env`:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | No | — | Full PostgreSQL connection string (e.g., `postgresql://user:password@host:5432/db`) |
| `POSTGRES_USER` | No | `equityuser` | PostgreSQL username (used if DATABASE_URL not set) |
| `POSTGRES_PASSWORD` | No | `equitypass` | PostgreSQL password (used if DATABASE_URL not set) |
| `POSTGRES_HOST` | No | `postgres` | PostgreSQL host (used if DATABASE_URL not set) |
| `POSTGRES_PORT` | No | `5432` | PostgreSQL port (used if DATABASE_URL not set) |
| `POSTGRES_DB` | No | `equitydb` | PostgreSQL database name (used if DATABASE_URL not set) |
| `SQL_ECHO` | No | `false` | Set to `true` to log SQL statements (debugging) |

**Example .env:**

```
DATABASE_URL=postgresql://equityuser:equitypass@postgres:5432/equitydb
SQL_ECHO=false
```

---

## Testing

Tests use an in-memory SQLite database (no external DB required):

```bash
cd backend
python3 -m pytest tests/test_persistence.py -v
```

This creates a fresh schema for each test, so tests are isolated and fast.

---

## Future Enhancements

- **Partitioning:** Partition `stock_prices` by date (monthly) for faster queries on large datasets
- **Aggregations:** Add pre-computed hourly/daily aggregates for faster UI queries
- **Comprehensive indexing:** Add indexes on (provider, timestamp) for cross-provider time-series comparisons
- **Materialized views:** Create views for common queries (e.g., latest price per stock, 52-week high/low)
