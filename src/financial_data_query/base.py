from abc import ABC, abstractmethod
import time
import os
import pandas as pd
from financial_data_query.constants import DATE_FORMAT
from financial_data_query.errors import FetchError


def _filter_by_date(df: pd.DataFrame, start: str | None, end: str | None) -> pd.DataFrame:
    """Filter DataFrame by date range. Shared across all fetchers."""
    if not (start or end):
        return df
    if not isinstance(df.index, pd.DatetimeIndex):
        df = df.copy()
        df.index = pd.to_datetime(df.index, errors="coerce")
    if getattr(df.index, "tz", None) is not None:
        df = df.copy()
        df.index = df.index.tz_localize(None)
    if start:
        df = df[df.index >= pd.Timestamp(start)]
    if end:
        df = df[df.index <= pd.Timestamp(end)]
    return df


def _check_cache_gaps(
    df: pd.DataFrame,
    start: str | None,
    end: str | None,
    frequency: str | None,
) -> bool:
    """Return True if cached data has suspicious gaps within the requested range.

    Used to detect when disk cache contains disjoint date ranges (e.g., 2020 + 2022)
    but not the data for an intermediate period (e.g., 2021) — the filter would return
    empty/partial results even though covers_start and covers_end both evaluate True.
    """
    if df.empty:
        return True
    if len(df) < 3:
        return False

    # Ensure DatetimeIndex for diff computation
    idx = df.index
    if not isinstance(idx, pd.DatetimeIndex):
        idx = pd.to_datetime(idx, errors="coerce")
        if idx.isna().any():
            return False  # Can't check gaps with invalid dates
    diffs = idx.to_series().diff().dt.days.dropna()
    if diffs.empty:
        return False

    median_diff = diffs.median()

    if frequency in ("daily", None):
        threshold = max(median_diff * 2, 7)
    elif frequency == "weekly":
        threshold = max(median_diff * 2, 21)
    elif frequency == "monthly":
        threshold = max(median_diff * 2, 60)
    else:
        return False

    return bool((diffs > threshold).any())


def _retry_fetch(fetch_func, max_retries=3):
    """Retry a fetch function with exponential backoff. Shared across all fetchers."""
    last_exc = None
    for attempt in range(max_retries):
        if attempt > 0:
            time.sleep(min(attempt * 2, 10))
        try:
            return fetch_func()
        except Exception as e:
            last_exc = e
    raise FetchError(f"Failed after {max_retries} retries: {last_exc}") from last_exc


def _cleanup_file(path: str) -> None:
    """Safely delete a temporary file. Shared across all fetchers."""
    try:
        os.unlink(path)
    except OSError:
        pass


def validate_symbol(symbol: str, symbol_map: dict, source_name: str) -> None:
    """Validate that a symbol exists in the symbol map. Raise FetchError if not."""
    if symbol not in symbol_map:
        raise FetchError(
            f"Invalid symbol '{symbol}' for {source_name}. "
            f"Must be one of: {', '.join(sorted(symbol_map.keys()))}"
        )


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
