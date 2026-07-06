import io

import pandas as pd
import requests
from financial_data_query.base import DataSourceFetcher, validate_symbol
from financial_data_query.errors import FetchError


_BASE_URL = "https://www.multpl.com"

_SYMBOL_MAP = {
    "sp500_ps": "s-p-500-price-to-sales/table/by-quarter",
    "sp500_div_yield": "s-p-500-dividend-yield/table/by-month",
    "sp500_pe": "s-p-500-pe-ratio/table/by-month",
    "shiller_pe": "shiller-pe/table/by-month",
    "sp500_earn_yield": "s-p-500-earnings-yield/table/by-month",
    "sp500_price": "s-p-500-historical-prices/table/by-month",
    "sp500_earn_growth": "s-p-500-earnings-growth/table/by-quarter",
}


class MultplFetcher(DataSourceFetcher):
    """Multpl (Rule #1) market valuation data.

    Scrapes HTML tables from multpl.com. Commonly used for SP500 PE ratio,
    Shiller PE (CAPE), dividend yield, etc. Data is fetched fresh each time
    and cached in the disk cache by the query system.
    """

    source_name = "multpl"
    # Full data caching: API returns ALL historical data for each symbol without date params.
    # _fetches_full_data = True: disk cache stores the complete data;
    # query layer filters by start/end on each read.
    _fetches_full_data = True

    def fetch(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> pd.DataFrame:
        validate_symbol(symbol, _SYMBOL_MAP, self.source_name)

        url = f"{_BASE_URL}/{_SYMBOL_MAP[symbol]}"
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as e:
            raise FetchError(f"Failed to fetch multpl data for '{symbol}': {e}") from e

        try:
            tables = pd.read_html(io.StringIO(resp.text), attrs={"id": "datatable"})
        except Exception as e:
            raise FetchError(f"Failed to parse HTML table for '{symbol}': {e}") from e

        if not tables:
            raise FetchError(f"No data table found for '{symbol}'")

        df = tables[0]
        if df.shape[1] < 2:
            raise FetchError(f"Table for '{symbol}' has fewer than 2 columns")

        df.columns = ["date", "value"] + list(df.columns[2:])
        df["date"] = pd.to_datetime(df["date"], format="mixed")
        df.set_index("date", inplace=True)

        value_str = df["value"].astype(str).str.replace(",", "").str.strip()
        value_str = value_str.str.replace("\u2002", "", regex=False)
        value_str = value_str.str.replace("†", "", regex=False)
        df["value"] = pd.to_numeric(value_str.str.rstrip("%"), errors="coerce")
        df = df.dropna(subset=["value"])

        df = df.sort_index()

        return df
