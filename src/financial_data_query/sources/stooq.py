import pandas as pd
import io
from financial_data_query.base import DataSourceFetcher
from financial_data_query.errors import FetchError


class StooqFetcher(DataSourceFetcher):
    source_name = "stooq"

    def _parse_csv(self, csv_content: str) -> pd.DataFrame:
        df = pd.read_csv(io.StringIO(csv_content))
        if df.empty:
            raise FetchError("Stooq returned empty data")
        df.columns = [c.strip() for c in df.columns]
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)
        numeric_cols = ["Open", "High", "Low", "Close", "Volume"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    def fetch(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> pd.DataFrame:
        raise NotImplementedError("fetch not yet implemented")
