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
    ) -> pd.DataFrame:
        """Fetch data and return as a DataFrame with DatetimeIndex."""
        ...

    def validate_config(self) -> bool:
        """Return True if required configuration is available."""
        return True
