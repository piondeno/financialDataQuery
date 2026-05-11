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

    def fetch(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
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

        if sub_field:
            col = _YAHOO_COLUMN_MAP.get(sub_field.lower())
            if col and col in df.columns:
                df = df[[col]]
            elif sub_field.lower() in [c.lower() for c in df.columns]:
                match_col = [c for c in df.columns if c.lower() == sub_field.lower()][0]
                df = df[[match_col]]

        return df
