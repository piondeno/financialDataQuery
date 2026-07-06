from collections import OrderedDict
import pandas as pd


class QueryCache:
    """In-memory LRU cache for query results.

    Uses OrderedDict for O(1) move-to-end on access. Cache key includes all
    query parameters to ensure exact match (source + symbol + date range + field + frequency).
    """

    def __init__(self, max_size: int = 128):
        self.   _cache: OrderedDict[tuple[str, str, str | None, str | None, str | None, str | None], pd.DataFrame] = OrderedDict()
        self._max_size = max_size

    def _key(
        self,
        source: str,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> tuple[str, str, str | None, str | None, str | None, str | None]:
        return (source, symbol, start, end, sub_field, frequency)

    def get(
        self,
        source: str,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> pd.DataFrame | None:
        key = self._key(source, symbol, start, end, sub_field, frequency)
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def set(
        self,
        source: str,
        symbol: str,
        df: pd.DataFrame,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> None:
        key = self._key(source, symbol, start, end, sub_field, frequency)
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = df
        while len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def clear(self) -> None:
        self._cache.clear()
