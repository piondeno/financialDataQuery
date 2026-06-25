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
    "mf_equity_domestic_total": ("mf", "Domestic Total domestic"),
    "mf_equity_domestic_large": ("mf", "Large cap"),
    "mf_equity_domestic_mid": ("mf", "Mid cap"),
    "mf_equity_domestic_small": ("mf", "Small cap"),
    "mf_equity_domestic_multi": ("mf", "Multi cap"),
    "mf_equity_domestic_other": ("mf", "Other"),
    "mf_equity_world_total": ("mf", "World Total world"),
    "mf_equity_world_developed": ("mf", "Developed markets"),
    "mf_equity_world_emerging": ("mf", "Emerging markets"),
    "mf_hybrid": ("mf", "Hybrid"),
    "mf_bond_total": ("mf", "Bond Total bond"),
    "mf_bond_taxable_total": ("mf", "Taxable Total taxable"),
    "mf_bond_taxable_investment": ("mf", "Investment grade"),
    "mf_bond_taxable_highyield": ("mf", "High yield"),
    "mf_bond_taxable_government": ("mf", "Government"),
    "mf_bond_taxable_multisector": ("mf", "Multisector"),
    "mf_bond_taxable_global": ("mf", "Global"),
    "mf_bond_municipal": ("mf", "Municipal"),
    # ETF
    "etf_total": ("etf", "Total ETFs"),
    "etf_equity_total": ("etf", "Equity Total"),
    "etf_equity_domestic": ("etf", "Domestic"),
    "etf_equity_world": ("etf", "World"),
    "etf_hybrid": ("etf", "Hybrid"),
    "etf_bond_total": ("etf", "Bond Total"),
    "etf_bond_taxable": ("etf", "Taxable"),
    "etf_bond_municipal": ("etf", "Municipal"),
    "etf_commodity": ("etf", "Commodity"),
    # Combined
    "combined_total": ("combined", "Total LT MF and ETF flows"),
    "combined_equity_total": ("combined", "Equity Total"),
    "combined_equity_domestic": ("combined", "Domestic"),
    "combined_equity_world": ("combined", "World"),
    "combined_hybrid": ("combined", "Hybrid"),
    "combined_bond_total": ("combined", "Bond Total"),
    "combined_bond_taxable": ("combined", "Taxable"),
    "combined_bond_municipal": ("combined", "Municipal"),
    "combined_commodity": ("combined", "Commodity"),
}


class IciFetcher(DataSourceFetcher):
    source_name = "ici"
    _excel_cache: dict[str, pd.DataFrame] = {}

    def _get_parsed_df(self, prefix: str) -> pd.DataFrame:
        if prefix not in self._excel_cache:
            tmp_path = self._download_excel(prefix)
            try:
                import xlrd  # noqa: F401
            except ImportError:
                raise FetchError(
                    "xlrd is required for ici source. "
                    "Install it with: pip install financial-data-query[ici]"
                )
            sheet_name = _SHEET_MAP[prefix]
            df = pd.read_excel(tmp_path, sheet_name=sheet_name, header=None)
            self._excel_cache[prefix] = df
        return self._excel_cache[prefix]

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
        df_raw = self._get_parsed_df(prefix)
        merged_columns = self._merge_headers(df_raw)
        date_col_values = df_raw.iloc[7:, 0]
        cleaned_dates = [
            str(v).strip() if pd.notna(v) else v for v in date_col_values
        ]
        dates = pd.to_datetime(cleaned_dates, format="%m/%d/%Y", errors="coerce")
        data_rows = df_raw.iloc[7:]
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

    def _download_excel(self, prefix: str) -> str:
        url = _URL_MAP[prefix]
        timestamp = int(time.time())
        tmp_path = f"/tmp/ici-{prefix}-{timestamp}.xls"
        try:
            urllib.request.urlretrieve(url, tmp_path)
        except Exception as e:
            raise FetchError(f"Failed to download ICI {prefix} Excel file: {e}") from e
        return tmp_path

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
