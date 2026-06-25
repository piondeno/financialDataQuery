import json
import requests
import pandas as pd
from financial_data_query.base import DataSourceFetcher
from financial_data_query.config import get_config
from financial_data_query.errors import ConfigError, FetchError


_FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"


class FredFetcher(DataSourceFetcher):
    source_name = "fred"

    def validate_config(self) -> bool:
        return get_config("FRED_API_KEY") is not None

    def _fetch_raw(self, params: dict) -> dict:
        api_key = get_config("FRED_API_KEY")
        if not api_key:
            raise ConfigError("FRED_API_KEY is not set. Set it in your environment or .env file.")

        params["api_key"] = api_key
        params["file_type"] = "json"

        resp = requests.get(_FRED_BASE_URL, params=params, timeout=30)

        if resp.status_code != 200:
            raise FetchError(f"FRED API error ({resp.status_code}): {resp.text[:300]}")

        return resp.json()

    def fetch(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> pd.DataFrame:
        params = {
            "series_id": symbol,
            "sort_order": "asc",
        }
        if start:
            params["observation_start"] = start
        if end:
            params["observation_end"] = end
        if frequency:
            params["frequency"] = frequency

        data = self._fetch_raw(params)
        observations = data.get("observations", [])

        if not observations:
            raise FetchError(f"No data returned for FRED series '{symbol}'")

        df = pd.DataFrame(observations, columns=["date", "value"])
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

        return df

    def batch_fetch(
        self,
        symbols: list[str],
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> dict[str, pd.DataFrame]:
        results = {}
        for symbol in symbols:
            try:
                results[symbol] = self.fetch(symbol, start, end, sub_field, frequency)
            except Exception as e:
                import warnings
                warnings.warn(f"Failed to fetch FRED series '{symbol}': {e}")
                results[symbol] = pd.DataFrame()
        return results
