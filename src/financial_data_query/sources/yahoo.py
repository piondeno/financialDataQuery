import pandas as pd
import yfinance as yf
from financial_data_query.base import DataSourceFetcher
from financial_data_query.constants import FREQUENCY_YAHOO_INTERVALS
from financial_data_query.errors import FetchError


_YAHOO_COLUMN_MAP = {
    "open": "Open",
    "high": "High",
    "low": "Low",
    "close": "Close",
    "volume": "Volume",
    "adjclose": "Adj Close",
}


class YahooFetcher(DataSourceFetcher):
    """Yahoo Finance market data via yfinance.

    Supports daily/weekly/monthly frequency. Use sub_field to extract
    a specific column (open/high/low/close/volume/adjclose).
    """

    source_name = "yahoo"
    _FREQUENCY_MAP = FREQUENCY_YAHOO_INTERVALS

    def fetch(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> pd.DataFrame:
        ticker = yf.Ticker(symbol)
        kwargs = {}
        if start:
            kwargs["start"] = start
        if end:
            kwargs["end"] = end

        if frequency:
            freq_key = frequency.lower()
            if freq_key not in self._FREQUENCY_MAP:
                raise FetchError(
                    f"Invalid frequency '{frequency}'. Must be one of: daily, weekly, monthly"
                )
            kwargs["interval"] = self._FREQUENCY_MAP[freq_key]

        df = ticker.history(**kwargs)

        if df.empty:
            raise FetchError(f"No data returned for Yahoo symbol '{symbol}'")

        if sub_field:
            col = _YAHOO_COLUMN_MAP.get(sub_field.lower())
            if col and col in df.columns:
                df = df[[col]]
            elif sub_field.lower() in [c.lower() for c in df.columns]:
                match_col = [c for c in df.columns if c.lower() == sub_field.lower()][0]
                df = df[[match_col]]

        return df
