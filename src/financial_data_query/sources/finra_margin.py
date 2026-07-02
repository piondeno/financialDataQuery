import time
import urllib.request
import pandas as pd
from financial_data_query.base import DataSourceFetcher, validate_symbol, _cleanup_file
from financial_data_query.constants import MONTH_FORMAT
from financial_data_query.errors import FetchError


_FINRA_URL = "https://www.finra.org/sites/default/files/2021-03/margin-statistics.xlsx"
_SHEET_NAME = "Customer Margin Balances"

_SYMBOL_MAP = {
    "debit_balances": "Debit Balances in Customers' Securities Margin Accounts",
    "free_credit_cash": "Free Credit Balances in Customers' Cash Accounts",
    "free_credit_margin": "Free Credit Balances in Customers' Securities Margin Accounts",
}


class FinraMarginFetcher(DataSourceFetcher):
    source_name = "finra_margin"
    _full_df_cache: pd.DataFrame | None = None
    _tmp_path_cache: str | None = None
    _fetches_full_data = True

    def _get_full_df(self) -> pd.DataFrame:
        if self._full_df_cache is not None:
            return self._full_df_cache
        try:
            import openpyxl  # noqa: F401
        except ImportError:
            raise FetchError(
                "openpyxl is required for finra_margin source. "
                "Install it with: pip install financial-data-query[finra_margin]"
            )
        timestamp = int(time.time())
        tmp_path = f"/tmp/margin-statistics-{timestamp}.xlsx"
        try:
            urllib.request.urlretrieve(_FINRA_URL, tmp_path)
            df = pd.read_excel(tmp_path, sheet_name=_SHEET_NAME, engine="openpyxl")
            df["Year-Month"] = (
                pd.to_datetime(df["Year-Month"], format=MONTH_FORMAT)
                + pd.offsets.MonthEnd(0)
            )
            df.set_index("Year-Month", inplace=True)
            self._full_df_cache = df
            self._tmp_path_cache = tmp_path
            return df
        except Exception as e:
            raise FetchError(f"Failed to download FINRA Excel file: {e}") from e

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
            df = self._get_full_df()
            column_name = _SYMBOL_MAP[symbol]
            result = df[[column_name]].rename(columns={column_name: "value"})
            result["value"] = pd.to_numeric(result["value"], errors="coerce")
            if result.empty:
                raise FetchError(
                    f"No data for symbol '{symbol}' in the given date range"
                )
            return result
        except FetchError:
            raise
        except Exception as e:
            raise FetchError(f"FINRA margin fetch failed: {e}") from e
        finally:
            if self._tmp_path_cache:
                _cleanup_file(self._tmp_path_cache)
                self._tmp_path_cache = None
