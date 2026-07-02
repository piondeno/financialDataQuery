import time
import urllib.request
import pandas as pd
from financial_data_query.base import DataSourceFetcher, validate_symbol, _cleanup_file
from financial_data_query.constants import ICI_DATE_FORMAT
from financial_data_query.errors import FetchError


_URL_MAP = {
    "mf": "https://www.ici.org/flows_data_2025.xls",
    "etf": "https://www.ici.org/etf_flows_data_2026.xls",
    "combined": "https://www.ici.org/combined_flows_data_2025.xls",
    "mmf_gov": "https://www.ici.org/statistical-report/mmf_data_hist_2026.xls",
    "mmf_prime": "https://www.ici.org/statistical-report/mmf_data_hist_2026.xls",
    "mmf_taxexempt": "https://www.ici.org/statistical-report/mmf_data_hist_2026.xls",
}

_CACHE_KEY_MAP = {
    "mf": "mf",
    "etf": "etf",
    "combined": "combined",
    "mmf_gov": "mmf",
    "mmf_prime": "mmf",
    "mmf_taxexempt": "mmf",
}

_CONFIG = {
    "mf": {"sheet": "Weekly MF Flow Estimates", "header_rows": [4, 5, 6], "date_format": ICI_DATE_FORMAT},
    "etf": {"sheet": "Weekly ETF Public Report", "header_rows": [4, 5, 6], "date_format": ICI_DATE_FORMAT},
    "combined": {"sheet": "Weekly MF & ETF Public Report", "header_rows": [4, 5, 6], "date_format": ICI_DATE_FORMAT},
    "mmf_gov": {"sheet": "Government Funds", "header_rows": [5, 6], "date_format": "mixed"},
    "mmf_prime": {"sheet": "Prime Funds", "header_rows": [5, 6], "date_format": "mixed"},
    "mmf_taxexempt": {"sheet": "Tax Exempt Funds", "header_rows": [5, 6], "date_format": "mixed"},
}

_SYMBOL_MAP = {
    # Mutual Fund
    "mf_total": "Total long-term",
    "mf_equity_total": "Equity Total equity",
    "mf_equity_domestic_total": "Domestic Total domestic",
    "mf_equity_domestic_large": "Large cap",
    "mf_equity_domestic_mid": "Mid cap",
    "mf_equity_domestic_small": "Small cap",
    "mf_equity_domestic_multi": "Multi cap",
    "mf_equity_domestic_other": "Other",
    "mf_equity_world_total": "World Total world",
    "mf_equity_world_developed": "Developed markets",
    "mf_equity_world_emerging": "Emerging markets",
    "mf_hybrid": "Hybrid",
    "mf_bond_total": "Bond Total bond",
    "mf_bond_taxable_total": "Taxable Total taxable",
    "mf_bond_taxable_investment": "Investment grade",
    "mf_bond_taxable_highyield": "High yield",
    "mf_bond_taxable_government": "Government",
    "mf_bond_taxable_multisector": "Multisector",
    "mf_bond_taxable_global": "Global",
    "mf_bond_municipal": "Municipal",
    # ETF
    "etf_total": "Total ETFs",
    "etf_equity_total": "Equity Total",
    "etf_equity_domestic": "Domestic",
    "etf_equity_world": "World",
    "etf_hybrid": "Hybrid",
    "etf_bond_total": "Bond Total",
    "etf_bond_taxable": "Taxable",
    "etf_bond_municipal": "Municipal",
    "etf_commodity": "Commodity",
    # Combined
    "combined_total": "Total LT MF and ETF flows",
    "combined_equity_total": "Equity Total",
    "combined_equity_domestic": "Domestic",
    "combined_equity_world": "World",
    "combined_hybrid": "Hybrid",
    "combined_bond_total": "Bond Total",
    "combined_bond_taxable": "Taxable",
    "combined_bond_municipal": "Municipal",
    "combined_commodity": "Commodity",
    # MMF - Government Funds
    "mmf_gov_total": "Total portfolio securities",
    "mmf_gov_treasury": "US Treasury debt",
    "mmf_gov_agency": "US Government agency debt",
    "mmf_gov_repo_total": "Repurchase agreement Total",
    "mmf_gov_repo_agency": "US Government agency",
    "mmf_gov_repo_treasury": "US Treasury",
    "mmf_gov_repo_other": "Other",
    "mmf_gov_cdp": "Certificate of deposit",
    "mmf_gov_ntd": "Non-negotiable time deposit",
    "mmf_gov_cp_total": "Commercial paper Total",
    "mmf_gov_cp_assetbacked": "Asset backed",
    "mmf_gov_cp_financial": "Financial company",
    "mmf_gov_cp_nonfinancial": "Non-Financial company",
    "mmf_gov_otherabs": "Other asset backed securities",
    "mmf_gov_muni_total": "Municipal debt Total",
    "mmf_gov_muni_vrdn": "Variable rate demand note",
    "mmf_gov_muni_other": "Other municipal security",
    "mmf_gov_tob": "Tender option bond",
    "mmf_gov_other_instrument": "Other instrument",
    "mmf_gov_icfa": "Insurance company funding agreement",
    "mmf_gov_inv_company": "Investment company",
    "mmf_gov_nonus_sov": "Non-US sovereign, sub sovereign, supra-national debt",
    "mmf_gov_other_note": "Other note",
    "mmf_gov_wam": "Weighted average maturity (WAM)",
    "mmf_gov_wal": "Weighted average life (WAL)",
    # MMF - Prime Funds
    "mmf_prime_total": "Total portfolio securities",
    "mmf_prime_treasury": "US Treasury debt",
    "mmf_prime_agency": "US Government agency debt",
    "mmf_prime_repo_total": "Repurchase agreement Total",
    "mmf_prime_repo_agency": "US Government agency",
    "mmf_prime_repo_treasury": "US Treasury",
    "mmf_prime_repo_other": "Other",
    "mmf_prime_cdp": "Certificate of deposit",
    "mmf_prime_ntd": "Non-negotiable time deposit",
    "mmf_prime_cp_total": "Commercial paper Total",
    "mmf_prime_cp_assetbacked": "Asset backed",
    "mmf_prime_cp_financial": "Financial company",
    "mmf_prime_cp_nonfinancial": "Non-Financial company",
    "mmf_prime_otherabs": "Other asset backed securities",
    "mmf_prime_muni_total": "Municipal debt Total",
    "mmf_prime_muni_vrdn": "Variable rate demand note",
    "mmf_prime_muni_other": "Other municipal security",
    "mmf_prime_tob": "Tender option bond",
    "mmf_prime_other_instrument": "Other instrument",
    "mmf_prime_icfa": "Insurance company funding agreement",
    "mmf_prime_inv_company": "Investment company",
    "mmf_prime_nonus_sov": "Non-US sovereign, sub sovereign, supra-national debt",
    "mmf_prime_other_note": "Other note",
    "mmf_prime_wam": "Weighted average maturity (WAM)",
    "mmf_prime_wal": "Weighted average life (WAL)",
    # MMF - Tax Exempt Funds
    "mmf_taxexempt_total": "Total portfolio securities",
    "mmf_taxexempt_treasury": "US Treasury debt",
    "mmf_taxexempt_agency": "US Government agency debt",
    "mmf_taxexempt_repo_total": "Repurchase agreement Total",
    "mmf_taxexempt_repo_agency": "US Government agency",
    "mmf_taxexempt_repo_treasury": "US Treasury",
    "mmf_taxexempt_repo_other": "Other",
    "mmf_taxexempt_cdp": "Certificate of deposit",
    "mmf_taxexempt_cp_total": "Commercial paper Total",
    "mmf_taxexempt_cp_assetbacked": "Asset backed",
    "mmf_taxexempt_cp_financial": "Financial company",
    "mmf_taxexempt_cp_nonfinancial": "Non-Financial company",
    "mmf_taxexempt_muni_total": "Municipal debt Total",
    "mmf_taxexempt_muni_vrdn": "Variable rate demand note",
    "mmf_taxexempt_muni_other": "Other municipal security",
    "mmf_taxexempt_other_instrument": "Other instrument",
    "mmf_taxexempt_inv_company": "Investment company",
    "mmf_taxexempt_tob": "Tender option bond",
    "mmf_taxexempt_other_note": "Other note",
    "mmf_taxexempt_wam": "Weighted average maturity (WAM)",
    "mmf_taxexempt_wal": "Weighted average life (WAL)",
}


class IciFetcher(DataSourceFetcher):
    source_name = "ici"
    _excel_cache: dict[str, dict[str, pd.DataFrame]] = {}
    _fetches_full_data = True
    _tmp_path_cache: str | None = None

    def _get_parsed_df(self, prefix: str) -> pd.DataFrame:
        cache_key = _CACHE_KEY_MAP[prefix]
        if cache_key not in self._excel_cache or prefix not in self._excel_cache[cache_key]:
            try:
                import xlrd  # noqa: F401
            except ImportError:
                raise FetchError(
                    "xlrd is required for ici source. "
                    "Install it with: pip install financial-data-query[ici]"
                )
            if cache_key not in self._excel_cache:
                self._excel_cache.clear()
                self._cleanup_current()
                tmp_path = self._download_excel(prefix)
                self._tmp_path_cache = tmp_path
                self._excel_cache[cache_key] = {}
            else:
                tmp_path = self._tmp_path_cache
            sheet_name = _CONFIG[prefix]["sheet"]
            df = pd.read_excel(tmp_path, sheet_name=sheet_name, header=None)
            self._excel_cache[cache_key][prefix] = df
        return self._excel_cache[cache_key][prefix]

    def _cleanup_current(self) -> None:
        if self._tmp_path_cache:
            _cleanup_file(self._tmp_path_cache)
            self._tmp_path_cache = None

    def cleanup(self) -> None:
        self._excel_cache.clear()
        self._cleanup_current()

    def fetch(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> pd.DataFrame:
        validate_symbol(symbol, _SYMBOL_MAP, self.source_name)

        try:
            column_name = _SYMBOL_MAP[symbol]
            prefix = symbol.split("_")[0]
            if prefix == "mmf":
                prefix = "mmf_" + symbol.split("_")[1]
            df_raw = self._get_parsed_df(prefix)
            header_rows = _CONFIG[prefix]["header_rows"]
            date_fmt = _CONFIG[prefix]["date_format"]
            merged_columns = self._merge_headers(df_raw, header_rows)
            date_col_values = df_raw.iloc[7:, 0]
            if date_fmt == "mixed":
                dates = pd.to_datetime(date_col_values, errors="coerce")
            else:
                cleaned_dates = [
                    str(v).strip() if pd.notna(v) else v
                    for v in date_col_values
                ]
                dates = pd.to_datetime(
                    cleaned_dates, format=date_fmt, errors="coerce"
                )
            data_rows = df_raw.iloc[7:]
            col_idx = merged_columns.get(column_name)
            if col_idx is None:
                raise FetchError(
                    f"Column '{column_name}' not found. Available: {list(merged_columns.keys())}"
                )
            values = pd.to_numeric(data_rows.iloc[:, col_idx], errors="coerce")
            result = pd.DataFrame({"value": values.values}, index=dates.values)
            result = result[~result.index.isna() & ~result["value"].isna()]
            if result.empty:
                raise FetchError(
                    f"No data for column '{column_name}' in the given date range"
                )
            return result
        except FetchError:
            raise
        except Exception as e:
            raise FetchError(f"ICI fetch failed: {e}") from e

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
    def _merge_headers(df: pd.DataFrame, header_rows: list[int]) -> dict[str, int]:
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
        _cleanup_file(path)
