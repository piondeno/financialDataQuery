# Disk Cache + Auto Frequency Selection Design

## Overview

Add a disk-based SQLite cache layer to the financial data query system, positioned between the existing in-memory LRU cache and API fetchers. This eliminates redundant API calls across sessions by persisting downloaded data per day. Additionally, for yahoo and stooq sources, auto-select an appropriate frequency based on the requested time range when the user does not specify one.

## Cache Architecture

### Three-layer query chain

```
query() -> in-memory cache (existing QueryCache)     HIT: return cached DataFrame
  MISS -> disk SQLite cache (/home/piondeno/.cache/financial_data_query/YYYY-MM-DD.db)
    HIT: filter by start/end, populate in-memory cache, return
    MISS: call API fetcher, merge into SQLite, filter by start/end, populate in-memory cache, return
```

### Storage path

- **Directory**: `/home/piondeno/.cache/financial_data_query`
- **File naming**: `{YYYY-MM-DD}.db` — one SQLite database per day
- **Old file cleanup**: On `DiskCache` initialization (first use), delete any `.db` files whose date does not match today

### Table naming convention

Each unique `(source, symbol, frequency)` combination gets its own table:

```
{source}_{sanitized_symbol}_{frequency}
```

Rules:
- `frequency`: for yahoo/stooq, the actual frequency string (`daily`, `weekly`, `monthly`, etc.); for all other sources, `none`
- `sanitized_symbol`: replace any non-alphanumeric character with `_` (e.g., `^GSPC` -> `_GSPC`)

### Table schema

```sql
CREATE TABLE IF NOT EXISTS {table_name} (
    date TEXT PRIMARY KEY,
    ...dynamic columns from DataFrame non-index columns
)
```

- `date` is always the primary key (derived from DatetimeIndex)
- Remaining columns come from the fetched DataFrame's column names
- On insert, use `INSERT OR REPLACE` to merge new data with existing data by date

## Auto Frequency Selection (yahoo & stooq only)

When `frequency` is not provided by the user and the source is yahoo or stooq:

| Requested time range | Default frequency |
|---|---|
| <= 1 year | `daily` |
| > 1 year, <= 5 years | `weekly` |
| > 5 years | `monthly` |

If the user explicitly provides a `frequency`, their value always takes precedence. If no start/end is provided (unbounded query), default to `daily`.

## Download & Merge Strategy

### yahoo / stooq (frequency-aware sources)

1. Determine frequency: use user-provided, or auto-select based on time range
2. Check disk cache for existing table `(source, symbol, frequency)`
3. If table exists with data, still fetch from API without date constraints to get full history
4. Merge new data into SQLite using `INSERT OR REPLACE` on `date` primary key

### Other sources (fred, tw_eco, tw_pmi, finra_margin, ici, macroMicro, us_treasury, multpl)

1. Check disk cache for existing table `(source, symbol, none)`
2. If table exists and is non-empty, read from cache and filter by start/end — no API call needed
3. If missing or empty, fetch full data from API (these APIs return all available data regardless of date params), store in SQLite

## Implementation Details

### New module: `disk_cache.py`

```python
class DiskCache:
    def __init__(self, cache_dir: str = "/home/piondeno/.cache/financial_data_query")
    
    def _table_name(self, source: str, symbol: str, frequency: str | None) -> str
    
    def get(
        self,
        source: str,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        frequency: str | None = None,
    ) -> pd.DataFrame | None
    
    def set(
        self,
        source: str,
        symbol: str,
        df: pd.DataFrame,
        frequency: str | None = None,
    ) -> None
    
    def _cleanup_old_files(self) -> None
```

### Modified module: `__init__.py`

Changes to the query flow:

1. Initialize global `_disk_cache = DiskCache()` alongside existing `_cache`
2. In `_single_query` and `_batch_query`, insert disk cache lookup between in-memory miss and API call
3. Add auto-frequency selection logic before dispatching to yahoo/stooq fetchers
4. After API fetch, persist data to disk cache before returning

### Unchanged modules

- All source fetchers (`yahoo.py`, `stooq.py`, `fred.py`, etc.) remain unchanged
- `cache.py` (in-memory QueryCache) remains unchanged
- `base.py`, `registry.py`, `errors.py`, `config.py` remain unchanged

## Error Handling

- SQLite operations wrapped in try/except; on failure, fall through to API fetch as if cache didn't exist
- Cache directory creation failures are non-fatal — proceed without disk caching
- Corrupt database files are deleted and recreated

## Testing Strategy

- Unit test `DiskCache` table naming sanitization
- Unit test auto-frequency selection logic with various date ranges
- Integration test: query -> cache miss -> API fetch -> cache hit on second call (mock API)
- Verify old file cleanup behavior
