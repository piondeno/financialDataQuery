import pandas as pd
from financial_data_query.config import load_env
from financial_data_query.registry import Registry
from financial_data_query.cache import QueryCache
from financial_data_query.base import DataSourceFetcher

load_env()

_cache = QueryCache(max_size=128)


def query(
    source: str,
    symbol: str,
    start: str | None = None,
    end: str | None = None,
    sub_field: str | None = None,
    use_cache: bool = True,
) -> pd.DataFrame:
    """Query financial data from a registered source.

    Args:
        source: Data source name (e.g., 'yahoo', 'fred')
        symbol: Ticker or series identifier
        start: Start date (YYYY-MM-DD), optional
        end: End date (YYYY-MM-DD), optional
        sub_field: Specific column to return, optional
        use_cache: Use in-memory cache, default True

    Returns:
        pandas DataFrame with DatetimeIndex
    """
    _import_sources()

    if use_cache:
        cached = _cache.get(source, symbol, start, end, sub_field)
        if cached is not None:
            return cached

    fetcher = Registry.get(source)
    df = fetcher.fetch(symbol, start=start, end=end, sub_field=sub_field)

    if use_cache:
        _cache.set(source, symbol, df, start=start, end=end, sub_field=sub_field)

    return df


def register_source(fetcher_cls: type[DataSourceFetcher]) -> None:
    """Register a custom data source fetcher class."""
    Registry.register(fetcher_cls)


def list_sources() -> list[str]:
    """List all registered data source names."""
    _import_sources()
    return Registry.list_sources()


def clear_cache() -> None:
    """Clear the in-memory query cache."""
    _cache.clear()


def _import_sources() -> None:
    from financial_data_query import sources  # noqa: F401
