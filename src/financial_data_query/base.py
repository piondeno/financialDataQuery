from abc import ABC, abstractmethod
import pandas as pd


class DataSourceFetcher(ABC):
    """Abstract base class for all data source fetchers."""

    source_name: str = ""

    @abstractmethod
    def fetch(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> pd.DataFrame:
        """Fetch data and return as a DataFrame with DatetimeIndex."""
        ...

    def batch_fetch(
        self,
        symbols: list[str],
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> dict[str, pd.DataFrame]:
        """Fetch data for multiple symbols, returning a dict mapping symbol to DataFrame.

        Default implementation calls fetch() for each symbol sequentially.
        Subclasses may override to optimize (e.g., shared browser session).
        """
        results = {}
        for symbol in symbols:
            results[symbol] = self.fetch(
                symbol, start=start, end=end, sub_field=sub_field, frequency=frequency
            )
        return results

    def validate_config(self) -> bool:
        """Return True if required configuration is available."""
        return True
