import pandas as pd
from financial_data_query.config import load_env
from financial_data_query.registry import Registry
from financial_data_query.cache import QueryCache
from financial_data_query.base import DataSourceFetcher

load_env()

_cache = QueryCache(max_size=128)


def _df_to_json(df: pd.DataFrame) -> list[dict]:
    """Convert a DataFrame to a list of dicts with lowercase keys."""
    reset = df.reset_index()
    if df.index.name is None:
        reset.columns = ["date"] + list(reset.columns[1:])
    reset.columns = [c.lower() if isinstance(c, str) else str(c) for c in reset.columns]
    records = reset.to_dict(orient="records")
    for record in records:
        for k, v in record.items():
            if isinstance(v, pd.Timestamp):
                record[k] = v.strftime("%Y-%m-%d")
    return records


def query(
    source: str,
    symbol: str | list[str],
    start: str | None = None,
    end: str | None = None,
    sub_field: str | None = None,
    frequency: str | None = None,
    output: str = "json",
    use_cache: bool = True,
) -> dict[str, list[dict]] | pd.DataFrame:
    """Query financial data from a registered source.

    Args:
        source: Data source name (e.g., 'yahoo', 'fred', 'stooq')
        symbol: Ticker/series identifier, or list of tickers for batch query
        start: Start date (YYYY-MM-DD), optional
        end: End date (YYYY-MM-DD), optional
        sub_field: Specific column to return, optional
        frequency: Data frequency, optional
        output: Output format - "json" (default) or "dataframe"
        use_cache: Use in-memory cache, default True

    Returns:
        JSON dict (default) or pandas DataFrame when output="dataframe"
    """
    _import_sources()
    fetcher = Registry.get(source)

    if isinstance(symbol, list):
        return _batch_query(
            fetcher, source, symbol, start, end, sub_field, frequency, output, use_cache
        )
    else:
        return _single_query(
            fetcher, source, symbol, start, end, sub_field, frequency, output, use_cache
        )


def _single_query(
    fetcher, source, symbol, start, end, sub_field, frequency, output, use_cache
):
    if use_cache:
        cached = _cache.get(source, symbol, start, end, sub_field, frequency)
        if cached is not None:
            if output == "json":
                return {symbol: _df_to_json(cached)}
            return cached

    df = fetcher.fetch(symbol, start=start, end=end, sub_field=sub_field, frequency=frequency)

    if use_cache:
        _cache.set(source, symbol, df, start=start, end=end, sub_field=sub_field, frequency=frequency)

    if output == "json":
        return {symbol: _df_to_json(df)}
    return df


def _batch_query(
    fetcher, source, symbols, start, end, sub_field, frequency, output, use_cache
):
    results = {}
    cached_symbols = []

    if use_cache:
        for s in symbols:
            cached = _cache.get(source, s, start, end, sub_field, frequency)
            if cached is not None:
                results[s] = cached
                cached_symbols.append(s)

    to_fetch = [s for s in symbols if s not in cached_symbols]
    if to_fetch:
        batch = fetcher.batch_fetch(
            to_fetch, start=start, end=end, sub_field=sub_field, frequency=frequency
        )
        results.update(batch)

        if use_cache:
            for s, df in batch.items():
                _cache.set(source, s, df, start=start, end=end, sub_field=sub_field, frequency=frequency)

    if output == "json":
        return {s: _df_to_json(df) for s, df in results.items()}

    if output == "dataframe":
        frames = []
        for s, df in results.items():
            frame = df.copy()
            frame["Symbol"] = s
            frames.append(frame)
        return pd.concat(frames)

    return results


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
