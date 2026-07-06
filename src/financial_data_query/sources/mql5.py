import time

import pandas as pd
import requests
from financial_data_query.base import DataSourceFetcher, validate_symbol
from financial_data_query.errors import FetchError

_BASE_URL = "https://www.mql5.com/en/economic-calendar/{country}/{indicator}/export"

_SYMBOL_MAP = {
    "eu_markit_composite_pmi": ("european-union", "markit-composite-pmi"),
    "eu_markit_manufacturing_pmi": ("european-union", "markit-manufacturing-pmi"),
    "china_caixin_composite_pmi": ("china", "caixin-composite-pmi"),
    "china_manufacturing_pmi": ("china", "manufacturing-pmi"),
    "china_caixin_manufacturing_pmi": ("china", "caixin-manufacturing-pmi"),
    "japan_markit_composite_pmi": ("japan", "markit-composite-pmi"),
    "brazil_markit_composite_pmi": ("brazil", "markit-composite-pmi"),
    "aus_cba_composite_pmi": ("australia", "commonwealth-bank-composite-pmi"),
    "us_ism_manufacturing_pmi": ("united-states", "ism-manufacturing-pmi"),
    "us_markit_manufacturing_pmi": ("united-states", "markit-manufacturing-pmi"),
    "us_markit_composite_pmi": ("united-states", "markit-composite-pmi"),
}


class Mql5Fetcher(DataSourceFetcher):
    """MQL5 economic calendar data.

    Downloads tab-separated text from mql5.com for various PMI indicators
    by country. Each symbol maps to a (country, indicator) URL path.
    The batch_fetch method adds a 2-second delay between symbols to avoid
    rate limiting.
    """

    source_name = "mql5"

    def fetch(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> pd.DataFrame:
        validate_symbol(symbol, _SYMBOL_MAP, self.source_name)

        country, indicator = _SYMBOL_MAP[symbol]
        url = _BASE_URL.format(country=country, indicator=indicator)

        try:
            resp = requests.get(
                url,
                timeout=30,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            raise FetchError(f"Failed to fetch mql5 data for '{symbol}': {e}") from e

        text = resp.text.strip()
        if not text:
            raise FetchError(f"Empty response from mql5 for '{symbol}'")

        try:
            df = self._parse_text(text)
        except Exception as e:
            raise FetchError(f"Failed to parse mql5 data for '{symbol}': {e}") from e

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
        for i, symbol in enumerate(symbols):
            try:
                results[symbol] = self.fetch(
                    symbol, start=start, end=end, sub_field=sub_field, frequency=frequency
                )
            except Exception as e:
                import warnings
                warnings.warn(f"Failed to fetch mql5 series '{symbol}': {e}")
                results[symbol] = pd.DataFrame()
            if i < len(symbols) - 1:
                time.sleep(2)
        return results

    @staticmethod
    def _parse_text(text: str) -> pd.DataFrame:
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        if not lines:
            raise ValueError("No data lines")

        header = [h.strip() for h in lines[0].split("\t")]
        if header != ["Date", "ActualValue", "ForecastValue", "PreviousValue"]:
            raise ValueError(f"Unexpected header: {header}")

        rows = []
        for line in lines[1:]:
            stripped = line.strip()
            if not stripped:
                continue

            parts = stripped.split("\t")
            date_str = parts[0].strip() if len(parts) > 0 else ""
            if not date_str:
                continue

            actual = parts[1].strip() if len(parts) > 1 else ""
            forecast = parts[2].strip() if len(parts) > 2 else ""
            previous = parts[3].strip() if len(parts) > 3 else ""

            rows.append([date_str, actual, forecast, previous])

        if not rows:
            raise ValueError("No valid data rows")

        df = pd.DataFrame(rows, columns=["date", "actual", "forecast", "previous"])
        df["date"] = pd.to_datetime(df["date"], format="%Y.%m.%d", errors="coerce")
        df = df.dropna(subset=["date"])
        df.set_index("date", inplace=True)

        for col in ["actual", "forecast", "previous"]:
            df[col] = pd.to_numeric(df[col].replace("", pd.NA), errors="coerce")

        df = df.sort_index()
        return df
