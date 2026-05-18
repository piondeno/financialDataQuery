import tempfile
import time
import urllib.request
import pandas as pd
from financial_data_query.base import DataSourceFetcher
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

        tmp_path = None
        try:
            tmp_path = self._download_excel()
            df = self._parse_excel(tmp_path, symbol, start, end)
            return df
        except FetchError:
            raise
        except Exception as e:
            raise FetchError(f"FINRA margin fetch failed: {e}") from e
        finally:
            if tmp_path:
                self._cleanup_file(tmp_path)

    def _download_excel(self) -> str:
        timestamp = int(time.time())
        tmp_path = f"/tmp/margin-statistics-{timestamp}.xlsx"
        try:
            urllib.request.urlretrieve(_FINRA_URL, tmp_path)
        except Exception as e:
            raise FetchError(f"Failed to download FINRA Excel file: {e}") from e
        return tmp_path

    def _parse_excel(
        self,
        tmp_path: str,
        symbol: str,
        start: str | None,
        end: str | None,
    ) -> pd.DataFrame:
        try:
            import openpyxl  # noqa: F401
        except ImportError:
            raise FetchError(
                "openpyxl is required for finra_margin source. "
                "Install it with: pip install financial-data-query[finra_margin]"
            )

        df = pd.read_excel(tmp_path, sheet_name=_SHEET_NAME, engine="openpyxl")

        df["Year-Month"] = (
            pd.to_datetime(df["Year-Month"], format="%Y-%m")
            + pd.offsets.MonthEnd(0)
        )
        df.set_index("Year-Month", inplace=True)

        column_name = _SYMBOL_MAP[symbol]
        df = df[[column_name]].rename(columns={column_name: "value"})
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

        if start:
            df = df[df.index >= pd.Timestamp(start)]
        if end:
            end_ts = pd.Timestamp(end) + pd.offsets.MonthEnd(0)
            df = df[df.index <= end_ts]

        if df.empty:
            raise FetchError(
                f"No data for symbol '{symbol}' in the given date range"
            )

        return df

    @staticmethod
    def _cleanup_file(path: str) -> None:
        try:
            import os
            os.unlink(path)
        except OSError:
            pass
