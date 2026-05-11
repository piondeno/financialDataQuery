import pandas as pd
import yfinance as yf
from financial_data_query.base import DataSourceFetcher
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
    source_name = "yahoo"

    _FREQUENCY_MAP = {
        "daily": "D",
        "weekly": "W-FRI",
        "monthly": "ME",
    }

    _OHLCV_AGG = {
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Volume": "sum",
    }

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

        df = ticker.history(**kwargs)

        if df.empty:
            raise FetchError(f"No data returned for Yahoo symbol '{symbol}'")

        if frequency:
            freq_key = frequency.lower()
            if freq_key not in self._FREQUENCY_MAP:
                raise FetchError(
                    f"Invalid frequency '{frequency}'. Must be one of: daily, weekly, monthly"
                )
            resample_rule = self._FREQUENCY_MAP[freq_key]
            df = df.resample(resample_rule).agg(self._OHLCV_AGG)
            df = df[df["Close"].notna()]

        if sub_field:
            col = _YAHOO_COLUMN_MAP.get(sub_field.lower())
            if col and col in df.columns:
                df = df[[col]]
            elif sub_field.lower() in [c.lower() for c in df.columns]:
                match_col = [c for c in df.columns if c.lower() == sub_field.lower()][0]
                df = df[[match_col]]

        return df
