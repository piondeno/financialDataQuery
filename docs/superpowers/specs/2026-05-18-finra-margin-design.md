# FinraMargin Data Source Design

## Overview

Add a new data source `finra_margin` that fetches monthly margin statistics from FINRA's published Excel file. The data covers three metrics of customer account balances from January 1997 to present, updated monthly.

## Source Details

- **Source name:** `finra_margin`
- **URL:** https://www.finra.org/sites/default/files/2021-03/margin-statistics.xlsx
- **Format:** Single-sheet Excel (`.xlsx`), sheet name `Customer Margin Balances`
- **Data range:** 1997-01 to present (352+ rows as of 2026-04)
- **Update frequency:** Monthly

## Symbols

| Symbol | Excel Column | Description |
|---|---|---|
| `debit_balances` | Debit Balances in Customers' Securities Margin Accounts | 客戶信貸 |
| `free_credit_cash` | Free Credit Balances in Customers' Cash Accounts | 現金賬戶 |
| `free_credit_margin` | Free Credit Balances in Customers' Securities Margin Accounts | 融資賬戶 |

## Architecture

Single class `FinraMarginFetcher` extending `DataSourceFetcher`. Follows the `FredFetcher` pattern: HTTP download -> parse -> return DataFrame.

### Data Flow

1. `fetch(symbol, start, end)` is called
2. Validate symbol against allowed list
3. Download Excel file to a temporary file in `/tmp/`
4. Parse with `pd.read_excel()` on the `Customer Margin Balances` sheet
5. Convert `Year-Month` column (format `YYYY-MM`) to `pd.DatetimeIndex` via `pd.PeriodIndex(freq="M").to_timestamp()`
6. Select the column matching the requested symbol
7. Filter by `start`/`end` date range if provided
8. Return single-column DataFrame with column name `value`
9. Delete the temporary file in a `finally` block

### Parameter Behavior

- **`symbol`** — required; must be one of the three symbols above
- **`start` / `end`** — optional; filters rows by date
- **`sub_field`** — not applicable; silently ignored
- **`frequency`** — not applicable (data is monthly); silently ignored

### Temporary File Handling

- File is downloaded to `/tmp/margin-statistics-{timestamp}.xlsx`
- Deleted in `finally` block regardless of success or failure
- No caching — each fetch downloads fresh data

### Error Handling

| Situation | Behavior |
|---|---|
| Invalid symbol | `FetchError` with list of valid symbols |
| Download failure (network/HTTP error) | `FetchError` with status code/message |
| Excel parsing failure | `FetchError` wrapping the original exception |
| Missing `openpyxl` | Graceful import failure; source not registered (same pattern as stooq) |

## Dependencies

- `openpyxl` — added as an optional dependency under `[finra_margin]` extras
- `requests` — already a core dependency, used for download
- `pandas` — already a core dependency, used for Excel parsing

## Files

| File | Action |
|---|---|
| `src/financial_data_query/sources/finra_margin.py` | Create — `FinraMarginFetcher` class |
| `src/financial_data_query/sources/__init__.py` | Modify — import and register with graceful fallback |
| `pyproject.toml` | Modify — add `finra_margin` optional dependency group |
| `tests/test_finra_margin.py` | Create — unit tests with mocked HTTP and file I/O |

## Testing

| Test | Description |
|---|---|
| `test_source_name` | Verifies `source_name == "finra_margin"` |
| `test_fetch_valid_symbol` | Mocks download, verifies DataFrame structure (DatetimeIndex, `value` column, numeric type) |
| `test_fetch_invalid_symbol` | Raises `FetchError` for unknown symbol |
| `test_fetch_date_filtering` | Verifies `start`/`end` filter rows correctly |
| `test_temp_file_cleaned_up` | Confirms temporary file is deleted after fetch |
| `test_download_failure` | HTTP error raises `FetchError` |
