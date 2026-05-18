# ICI Data Source Design

## Overview

Add ICI (Investment Company Institute) as a new data source, registered under `"ici"`. Three XLS files provide monthly and weekly fund flow data for mutual funds, ETFs, and a combined view.

## Architecture

Single `IciFetcher` class extending `DataSourceFetcher`, following the same download-parse-cleanup pattern as `FinraMarginFetcher`.

- **File:** `src/financial_data_query/sources/ici.py`
- **Registration:** `src/financial_data_query/sources/__init__.py`
- **Optional dependency:** `xlrd>=2.0.1` (required for `.xls` format)
- **Tests:** `tests/test_ici.py`

## Data Sources

| File | URL | Sheet |
|------|-----|-------|
| Combined MF & ETF | `https://www.ici.org/combined_flows_data_2025.xls` | Weekly MF & ETF Public Report |
| Mutual Fund Flows | `https://www.ici.org/flows_data_2025.xls` | Weekly MF Flow Estimates |
| ETF Flows | `https://www.ici.org/etf_flows_data_2026.xls` | Weekly ETF Public Report |

## Symbol Mapping

### Mutual Fund (`mf_*`)

| Symbol | Column (merged header) |
|--------|------------------------|
| `mf_total` | Total long-term |
| `mf_equity_total` | Total equity |
| `mf_equity_domestic_total` | Total domestic |
| `mf_equity_domestic_large` | Large cap |
| `mf_equity_domestic_mid` | Mid cap |
| `mf_equity_domestic_small` | Small cap |
| `mf_equity_domestic_multi` | Multi cap |
| `mf_equity_domestic_other` | Other |
| `mf_equity_world_total` | Total world |
| `mf_equity_world_developed` | Developed markets |
| `mf_equity_world_emerging` | Emerging markets |
| `mf_hybrid` | Hybrid |
| `mf_bond_total` | Total bond |
| `mf_bond_taxable_total` | Total taxable |
| `mf_bond_taxable_investment` | Investment grade |
| `mf_bond_taxable_highyield` | High yield |
| `mf_bond_taxable_government` | Government |
| `mf_bond_taxable_multisector` | Multisector |
| `mf_bond_taxable_global` | Global |
| `mf_bond_municipal` | Municipal |

### ETF (`etf_*`)

| Symbol | Column (merged header) |
|--------|------------------------|
| `etf_total` | Total ETFs |
| `etf_equity_total` | Equity Total |
| `etf_equity_domestic` | Equity Domestic |
| `etf_equity_world` | Equity World |
| `etf_hybrid` | Hybrid |
| `etf_bond_total` | Bond Total |
| `etf_bond_taxable` | Bond Taxable |
| `etf_bond_municipal` | Bond Municipal |
| `etf_commodity` | Commodity |

### Combined (`combined_*`)

| Symbol | Column (merged header) |
|--------|------------------------|
| `combined_total` | Total LT MF and ETF flows |
| `combined_equity_total` | Equity Total |
| `combined_equity_domestic` | Equity Domestic |
| `combined_equity_world` | Equity World |
| `combined_hybrid` | Hybrid |
| `combined_bond_total` | Bond Total |
| `combined_bond_taxable` | Bond Taxable |
| `combined_bond_municipal` | Bond Municipal |
| `combined_commodity` | Commodity |

## Data Flow

1. `fetch(symbol)` receives a symbol (e.g., `mf_equity_total`)
2. Prefix determines which XLS file to download (`mf` → mutual fund, `etf` → ETF, `combined` → combined)
3. Download XLS to `/tmp/ici-{prefix}-{timestamp}.xls`
4. Parse with `pd.read_excel()`, merge 3-row headers into full column names
5. Extract the matching column, combine monthly and weekly rows into one DataFrame
6. Filter by `start`/`end` if provided
7. Return DataFrame with DatetimeIndex and single `value` column
8. Clean up temp file in `finally` block

## Header Parsing

Headers span rows 4-6 (0-indexed). Merge logic:
- Row 4: top-level category (e.g., "Equity", "Bond")
- Row 5: sub-category (e.g., "Domestic", "World", "Taxable")
- Row 6: leaf category (e.g., "Large cap", "Mid cap")
- Merge by joining non-NaN values across the three rows with space separator

## Error Handling

| Condition | Error |
|-----------|-------|
| Unknown symbol | `FetchError` with list of valid symbols |
| Download failure | `FetchError` |
| `xlrd` not installed | `FetchError` with install instruction |
| No data in date range | `FetchError` |

## Testing

- Mock `urllib.request.urlretrieve` with sample XLS data
- Verify each symbol maps to correct column
- Test batch query with multiple symbols
- Verify temp file cleanup

## Dependencies

Add to `pyproject.toml`:
```toml
ici = [
    "xlrd>=2.0.1",
]
```
