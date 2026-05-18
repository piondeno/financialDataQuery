import os
import time
import urllib.request
import pandas as pd
from financial_data_query.base import DataSourceFetcher
from financial_data_query.errors import FetchError


_URL_MAP = {
    "mf": "https://www.ici.org/flows_data_2025.xls",
    "etf": "https://www.ici.org/etf_flows_data_2026.xls",
    "combined": "https://www.ici.org/combined_flows_data_2025.xls",
}

_SHEET_MAP = {
    "mf": "Weekly MF Flow Estimates",
    "etf": "Weekly ETF Public Report",
    "combined": "Weekly MF & ETF Public Report",
}

_SYMBOL_MAP = {
    # Mutual Fund
    "mf_total": ("mf", "Total long-term"),
    "mf_equity_total": ("mf", "Equity Total equity"),
    "mf_equity_domestic_total": ("mf", "Equity Domestic Total domestic"),
    "mf_equity_domestic_large": ("mf", "Equity Domestic Large cap"),
    "mf_equity_domestic_mid": ("mf", "Equity Domestic Mid cap"),
    "mf_equity_domestic_small": ("mf", "Equity Domestic Small cap"),
    "mf_equity_domestic_multi": ("mf", "Equity Domestic Multi cap"),
    "mf_equity_domestic_other": ("mf", "Equity Domestic Other"),
    "mf_equity_world_total": ("mf", "Equity Total world"),
    "mf_equity_world_developed": ("mf", "Equity Developed markets"),
    "mf_equity_world_emerging": ("mf", "Equity Emerging markets"),
    "mf_hybrid": ("mf", "Hybrid"),
    "mf_bond_total": ("mf", "Bond Total bond"),
    "mf_bond_taxable_total": ("mf", "Bond Total taxable"),
    "mf_bond_taxable_investment": ("mf", "Bond Investment grade"),
    "mf_bond_taxable_highyield": ("mf", "Bond High yield"),
    "mf_bond_taxable_government": ("mf", "Bond Government"),
    "mf_bond_taxable_multisector": ("mf", "Bond Multisector"),
    "mf_bond_taxable_global": ("mf", "Bond Global"),
    "mf_bond_municipal": ("mf", "Municipal"),
    # ETF
    "etf_total": ("etf", "Total ETFs"),
    "etf_equity_total": ("etf", "Equity Total"),
    "etf_equity_domestic": ("etf", "Equity Domestic"),
    "etf_equity_world": ("etf", "Equity World"),
    "etf_hybrid": ("etf", "Hybrid"),
    "etf_bond_total": ("etf", "Bond Total"),
    "etf_bond_taxable": ("etf", "Bond Taxable"),
    "etf_bond_municipal": ("etf", "Bond Municipal"),
    "etf_commodity": ("etf", "Commodity"),
    # Combined
    "combined_total": ("combined", "Total LT MF and ETF flows"),
    "combined_equity_total": ("combined", "Equity Total"),
    "combined_equity_domestic": ("combined", "Equity Domestic"),
    "combined_equity_world": ("combined", "Equity World"),
    "combined_hybrid": ("combined", "Hybrid"),
    "combined_bond_total": ("combined", "Bond Total"),
    "combined_bond_taxable": ("combined", "Bond Taxable"),
    "combined_bond_municipal": ("combined", "Bond Municipal"),
    "combined_commodity": ("combined", "Commodity"),
}


class IciFetcher(DataSourceFetcher):
    source_name = "ici"

    def fetch(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> pd.DataFrame:
        if symbol not in _SYMBOL_MAP:
            raise FetchError(
                f"Invalid symbol '{symbol}'. "
                f"Must be one of: {', '.join(sorted(_SYMBOL_MAP.keys()))}"
            )

        prefix, column_name = _SYMBOL_MAP[symbol]
        tmp_path = None
        try:
            tmp_path = self._download_excel(prefix)
            df = self._parse_excel(tmp_path, prefix, column_name, start, end)
            return df
        except FetchError:
            raise
        except Exception as e:
            raise FetchError(f"ICI fetch failed for '{symbol}': {e}") from e
        finally:
            if tmp_path:
                self._cleanup_file(tmp_path)

    def _download_excel(self, prefix: str) -> str:
        url = _URL_MAP[prefix]
        timestamp = int(time.time())
        tmp_path = f"/tmp/ici-{prefix}-{timestamp}.xls"
        try:
            urllib.request.urlretrieve(url, tmp_path)
        except Exception as e:
            raise FetchError(f"Failed to download ICI {prefix} Excel file: {e}") from e
        return tmp_path

    def _parse_excel(
        self,
        tmp_path: str,
        prefix: str,
        column_name: str,
        start: str | None,
        end: str | None,
    ) -> pd.DataFrame:
        try:
            import xlrd  # noqa: F401
        except ImportError:
            raise FetchError(
                "xlrd is required for ici source. "
                "Install it with: pip install financial-data-query[ici]"
            )

        sheet_name = _SHEET_MAP[prefix]
        df = pd.read_excel(tmp_path, sheet_name=sheet_name, header=None)

        merged_columns = self._merge_headers(df)
        date_col_values = df.iloc[7:, 0]

        dates = pd.to_datetime(date_col_values, format="%m/%d/%Y", errors="coerce")
        data_rows = df.iloc[7:]

        col_idx = merged_columns.get(column_name)
        if col_idx is None:
            raise FetchError(
                f"Column '{column_name}' not found. Available: {list(merged_columns.keys())}"
            )

        values = pd.to_numeric(data_rows.iloc[:, col_idx], errors="coerce")
        result = pd.DataFrame({"value": values.values}, index=dates.values)
        result = result[~result.index.isna() & ~result["value"].isna()]

        if start:
            result = result[result.index >= pd.Timestamp(start)]
        if end:
            result = result[result.index <= pd.Timestamp(end)]

        if result.empty:
            raise FetchError(
                f"No data for column '{column_name}' in the given date range"
            )

        return result

    @staticmethod
    def _merge_headers(df: pd.DataFrame) -> dict[str, int]:
        header_rows = [4, 5, 6]
        merged = {}
        for col_idx in range(df.shape[1]):
            parts = []
            for row_idx in header_rows:
                if row_idx < len(df):
                    val = df.iloc[row_idx, col_idx]
                    if pd.notna(val) and str(val).strip():
                        normalized = " ".join(str(val).split())
                        parts.append(normalized)
            if parts:
                merged[" ".join(parts)] = col_idx
        return merged

    @staticmethod
    def _cleanup_file(path: str) -> None:
        try:
            os.unlink(path)
        except OSError:
            pass
