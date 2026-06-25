import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from financial_data_query.base import DataSourceFetcher
from financial_data_query.errors import FetchError


_OPTIONCHARTS_API_URL = "https://optioncharts.io/async/option_history_table"


class OptionchartsFetcher(DataSourceFetcher):
    source_name = "optioncharts"

    def _fetch_raw(self, symbol: str) -> dict:
        params = {
            "ticker": symbol,
            "period": "max",
        }

        resp = requests.get(_OPTIONCHARTS_API_URL, params=params, timeout=30)

        if resp.status_code != 200:
            raise FetchError(f"OptionCharts API error ({resp.status_code}): {resp.text[:300]}")

        return {"html": resp.text}

    def _extract_main_value(self, text: str) -> str:
        """Extract the main value from text that may contain change info."""
        match = re.match(r"([+-]?\d[\d,.]*[MKmkbB]?\.?\d*)", text)
        if match:
            return match.group(1)
        return text

    def fetch(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> pd.DataFrame:
        data = self._fetch_raw(symbol)

        soup = BeautifulSoup(data["html"], "html.parser")
        table = soup.find(id="option-history-table-id")

        if not table:
            raise FetchError(f"No table data found for OptionCharts symbol '{symbol}'")

        rows = []
        for row in table.find_all("tr"):
            cells = row.find_all(["th", "td"])
            row_data = [cell.get_text(strip=True) for cell in cells]
            rows.append(row_data)

        if not rows:
            raise FetchError(f"No data returned for OptionCharts symbol '{symbol}'")

        columns = rows[0]
        num_cols = len(columns)

        data_rows = [row for row in rows[1:] if len(row) == num_cols]

        df = pd.DataFrame(data_rows, columns=columns)

        df.columns = [c.replace("\n", " ").strip() for c in df.columns]
        rename_map = {
            "Option VolumeTotal": "Option Volume Total",
            "Option VolumePut-Call Ratio": "Option Volume Put-Call Ratio",
            "OITotal": "OI Total",
            "OIPut-Call Ratio": "OI Put-Call Ratio",
        }
        df.rename(columns=rename_map, inplace=True)

        first_col = df.columns[0]
        df.rename(columns={first_col: "Date"}, inplace=True)
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)

        numeric_cols = [
            "Close Price",
            "Option Volume Total",
            "Option Volume Put-Call Ratio",
            "OI Total",
            "OI Put-Call Ratio",
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].apply(self._extract_main_value)
                df[col] = pd.to_numeric(df[col].str.replace(",", "").str.replace("M", "e6").str.replace("K", "e3"), errors="coerce")

        if sub_field:
            if sub_field in df.columns:
                return df[[sub_field]]
            else:
                raise FetchError(f"Sub-field '{sub_field}' not found. Available: {list(df.columns)}")

        available_cols = [
            "Close Price",
            "Option Volume Total",
            "Option Volume Put-Call Ratio",
            "OI Total",
            "OI Put-Call Ratio",
        ]
        df = df[[col for col in available_cols if col in df.columns]]
        df.sort_index(inplace=True)

        if frequency and frequency.lower() in ("weekly", "monthly", "quarterly"):
            freq_map = {
                "weekly": "W-FRI",
                "monthly": "ME",
                "quarterly": "QE",
            }
            freq_alias = freq_map.get(frequency.lower())
            if freq_alias:
                agg_dict = {}
                for col in df.columns:
                    if "Volume" in col and "Ratio" in col:
                        agg_dict[col] = "last"
                    elif "Volume" in col:
                        agg_dict[col] = "sum"
                    else:
                        agg_dict[col] = "last"
                df = df.resample(freq_alias).agg(agg_dict).dropna()

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
                warnings.warn(f"Failed to fetch OptionCharts symbol '{symbol}': {e}")
                results[symbol] = pd.DataFrame()
        return results
