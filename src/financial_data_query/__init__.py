from datetime import timedelta
import pandas as pd
from financial_data_query.config import load_env
from financial_data_query.registry import Registry
from financial_data_query.cache import QueryCache
from financial_data_query.base import DataSourceFetcher
from financial_data_query.disk_cache import DiskCache

load_env()

_cache = QueryCache(max_size=128)
_disk_cache = DiskCache()

_FREQUENCY_AWARE_SOURCES = {"yahoo", "stooq"}


def _has_batch_cache(fetcher, source):
    """Check if fetcher has batch caching capability (attr exists AND has value)."""
    for attr in ('_full_table_cache', '_full_data_cache', '_full_df_cache'):
        val = getattr(fetcher, attr, None)
        if val is not None:
            return True
    return False


def _get_batch_cache(fetcher, source):
    """Check if fetcher has a batch cache and return the full table."""
    for attr in ('_full_table_cache', '_full_data_cache', '_full_df_cache'):
        cache = getattr(fetcher, attr, None)
        if hasattr(cache, 'get'):  # dict-like
            if cache.get(source) is not None:
                return cache[source]
        elif cache is not None and hasattr(cache, 'shape'):  # DataFrame
            return cache
    return None


def _set_batch_cache(fetcher, source, df):
    """Store full table in the fetcher's batch cache."""
    for attr in ('_full_table_cache', '_full_data_cache', '_full_df_cache'):
        cache = getattr(fetcher, attr, None)
        if hasattr(cache, '__setitem__'):  # dict-like
            cache[source] = df
            return True
    return False


def _auto_frequency(
    source: str, start: str | None, end: str | None, frequency: str | None
) -> str | None:
    if frequency:
        return frequency
    if source not in _FREQUENCY_AWARE_SOURCES:
        return None
    if not start or not end:
        return "daily"

    try:
        delta = pd.Timestamp(end) - pd.Timestamp(start)
    except Exception:
        return "daily"

    days = delta.days
    if days <= 365:
        return "daily"
    elif days <= 1825:
        return "weekly"
    else:
        return "monthly"


def _df_to_json(df: pd.DataFrame) -> list[dict]:
    """Convert a DataFrame to a list of dicts with lowercase keys."""
    reset = df.reset_index()
    reset.rename(columns={reset.columns[0]: "date"}, inplace=True)
    if len(reset.columns) == 2:
        reset.rename(columns={reset.columns[1]: "value"}, inplace=True)
    else:
        reset.columns = [c.lower() if isinstance(c, str) else str(c) for c in reset.columns]
    records = reset.to_dict(orient="records")
    for record in records:
        for k, v in record.items():
            if isinstance(v, pd.Timestamp):
                record[k] = v.strftime("%Y-%m-%d")
    return records


def _filter_by_date(df: pd.DataFrame, start: str | None, end: str | None) -> pd.DataFrame:
    if df is None or len(df) == 0:
        return df
    if not (start or end):
        return df
    # Normalize index: ensure DatetimeIndex, drop tz (compare against naive Timestamps)
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


def _apply_sub_field(df: pd.DataFrame, sub_field: str | None) -> pd.DataFrame:
    if not sub_field or sub_field not in df.columns:
        return df
    return df[[sub_field]]


def _single_query(
    fetcher, source, symbol, start, end, sub_field, frequency, output, use_cache
):
    effective_freq = _auto_frequency(source, start, end, frequency)

    if use_cache:
        cached = _cache.get(source, symbol, start, end, sub_field, effective_freq)
        if cached is not None:
            if output == "json":
                return {symbol: _df_to_json(cached)}
            return cached

    full_df = None

    if use_cache:
        # Step 1: Check in-memory batch cache (same process)
        if _has_batch_cache(fetcher, source):
            full_table = _get_batch_cache(fetcher, source)
            if full_table is not None:
                match_cols = [c for c in full_table.columns if c == symbol or c.startswith(symbol + "_")]
                if match_cols:
                    full_df = full_table[[match_cols[0]]].rename(columns={match_cols[0]: "value"}) if len(match_cols) == 1 else full_table[match_cols].copy()

        # Step 2: Check disk cache for full table (cross-process / empty in-memory)
        if full_df is None:
            disk_df = _disk_cache.get(source, f"_{source}_full_table", frequency=effective_freq)
            if disk_df is not None and len(disk_df):
                covers_start = not start or disk_df.index.min() <= pd.Timestamp(start)
                covers_end = not end or disk_df.index.max() >= pd.Timestamp(end)
                if covers_start and covers_end:
                    filtered = _filter_by_date(disk_df, start, end)
                    match_cols = [c for c in filtered.columns if c == symbol or c.startswith(symbol + "_")]
                    if match_cols:
                        full_df = filtered[[match_cols[0]]].rename(columns={match_cols[0]: "value"}) if len(match_cols) == 1 else filtered[match_cols].copy()

        # Step 3: Check disk cache for individual symbol
        if full_df is None:
            disk_df = _disk_cache.get(source, symbol, frequency=effective_freq)
            if disk_df is not None and len(disk_df):
                covers_start = not start or disk_df.index.min() <= pd.Timestamp(start)
                covers_end = not end or disk_df.index.max() >= pd.Timestamp(end)
                if covers_start and covers_end:
                    filtered = _filter_by_date(disk_df, start, end)
                    if len(filtered):
                        full_df = filtered

        if full_df is None:
            # Check if fetcher has batch cache (full table already loaded in-memory)
            has_batch_cache = _has_batch_cache(fetcher, source)

            df_fetched = None
            if has_batch_cache:
                batch_df = _get_batch_cache(fetcher, source)
                if batch_df is not None and symbol in batch_df.columns:
                    df_fetched = batch_df[[symbol]].rename(columns={symbol: "value"})

            if df_fetched is None:
                df_fetched = fetcher.fetch(
                    symbol, start=start, end=end, sub_field=sub_field, frequency=effective_freq
                )

            full_df = _filter_by_date(df_fetched, start, end)

            if use_cache:
                try:
                    # For batch cache sources, store full table under source-level key
                    # After fetcher.fetch(), the full table should be in fetcher's internal cache
                    if _has_batch_cache(fetcher, source):
                        # Directly access cache attributes to avoid nested function shadowing
                        for attr in ('_full_table_cache', '_full_data_cache', '_full_df_cache'):
                            full_table = getattr(fetcher, attr, None)
                            if full_table is not None and hasattr(full_table, 'get'):
                                cached_df = full_table.get(source)
                                if cached_df is not None and len(cached_df):
                                    _disk_cache.set(source, f"_{source}_full_table", cached_df, frequency=effective_freq)
                                    break
                        else:
                            # Fallback to module-level helper
                            full_table = _get_batch_cache(fetcher, source)
                            if full_table is not None and len(full_table):
                                _disk_cache.set(source, f"_{source}_full_table", full_table, frequency=effective_freq)
                    else:
                        existing = _disk_cache.get(source, symbol, frequency=effective_freq)
                        if existing is not None and len(existing):
                            merged = pd.concat([existing, df_fetched])
                            merged = merged[~merged.index.duplicated(keep="first")]
                            merged.sort_index(inplace=True)
                            _disk_cache.set(source, symbol, merged, frequency=effective_freq)
                        else:
                            _disk_cache.set(source, symbol, df_fetched, frequency=effective_freq)
                except Exception:
                    pass

    if sub_field and len(full_df.columns) > 1:
        full_df = _apply_sub_field(full_df, sub_field)

    if use_cache:
        _cache.set(
            source, symbol, full_df, start=start, end=end,
            sub_field=sub_field, frequency=effective_freq
        )

    if output == "json":
        return {symbol: _df_to_json(full_df)}
    return full_df


def _batch_query(
    fetcher, source, symbols, start, end, sub_field, frequency, output, use_cache
):
    effective_freq = _auto_frequency(source, start, end, frequency)
    results = {}
    cached_symbols = []

    if use_cache:
        for s in symbols:
            cached = _cache.get(source, s, start, end, sub_field, effective_freq)
            if cached is not None:
                results[s] = cached
                cached_symbols.append(s)

    to_fetch = [s for s in symbols if s not in cached_symbols]

    disk_hit_symbols = []
    if use_cache and to_fetch:
        # Step 1: Check in-memory batch cache (same process)
        in_memory_hit = False
        if _has_batch_cache(fetcher, source):
            full_table = _get_batch_cache(fetcher, source)
            if full_table is not None:
                in_memory_hit = True
                for s in to_fetch:
                    if s in full_table.columns:
                        filtered = full_table[[s]].copy()
                        filtered = filtered.rename(columns={s: "value"})
                        filtered = _filter_by_date(filtered, start, end)
                        if sub_field and len(filtered.columns) > 1:
                            filtered = _apply_sub_field(filtered, sub_field)
                        if len(filtered):
                            results[s] = filtered
                            disk_hit_symbols.append(s)

        # Step 2: Check disk cache for full table (cross-process)
        # Also needed when in-memory cache exists but is empty
        for s in to_fetch:
            if s in disk_hit_symbols:
                continue
            disk_df = _disk_cache.get(source, f"_{source}_full_table", frequency=effective_freq)
            if disk_df is not None and len(disk_df):
                covers_start = not start or disk_df.index.min() <= pd.Timestamp(start)
                covers_end = not end or disk_df.index.max() >= pd.Timestamp(end)
                if covers_start and covers_end:
                    filtered = _filter_by_date(disk_df, start, end)
                    # For sources like moea where columns are "commodity_region" format,
                    # also check for columns that start with the symbol name
                    match_cols = [c for c in filtered.columns if c == s or c.startswith(s + "_")]
                    if match_cols:
                        if len(match_cols) == 1:
                            sub_df = filtered[[match_cols[0]]].rename(columns={match_cols[0]: "value"})
                        else:
                            sub_df = filtered[match_cols].copy()
                        sub_df = _filter_by_date(sub_df, start, end)
                        if sub_field and len(sub_df.columns) > 1:
                            sub_df = _apply_sub_field(sub_df, sub_field)
                        if len(sub_df):
                            results[s] = sub_df
                            disk_hit_symbols.append(s)
                            continue

        # Step 3: Check disk cache for individual symbol
        for s in to_fetch:
            if s in disk_hit_symbols:
                continue
            disk_df = _disk_cache.get(source, s, frequency=effective_freq)
            if disk_df is not None and len(disk_df):
                covers_start = not start or disk_df.index.min() <= pd.Timestamp(start)
                covers_end = not end or disk_df.index.max() >= pd.Timestamp(end)
                if covers_start and covers_end:
                    filtered = _filter_by_date(disk_df, start, end)
                    if sub_field and len(filtered.columns) > 1:
                        filtered = _apply_sub_field(filtered, sub_field)
                    if len(filtered):
                        results[s] = filtered

    still_to_fetch = [s for s in to_fetch if s not in disk_hit_symbols]
    if still_to_fetch:
        batch = fetcher.batch_fetch(
            still_to_fetch, sub_field=sub_field, frequency=effective_freq
        )

        for s, df in batch.items():
            filtered = _filter_by_date(df, start, end)
            if sub_field and len(filtered.columns) > 1:
                filtered = _apply_sub_field(filtered, sub_field)
            results[s] = filtered

        # Save full table to disk cache once after batch fetch
        if use_cache and _has_batch_cache(fetcher, source):
            for attr in ('_full_table_cache', '_full_data_cache', '_full_df_cache'):
                full_table = getattr(fetcher, attr, None)
                if full_table is not None and hasattr(full_table, 'get'):
                    cached_df = full_table.get(source)
                    if cached_df is not None and len(cached_df):
                        try:
                            _disk_cache.set(source, f"_{source}_full_table", cached_df, frequency=effective_freq)
                        except Exception:
                            pass
                        break

        if use_cache:
            for s, df in results.items():
                if s not in cached_symbols and s not in disk_hit_symbols:
                    _cache.set(
                        source, s, df, start=start, end=end,
                        sub_field=sub_field, frequency=effective_freq
                    )

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


def clear_disk_cache() -> None:
    from datetime import date
    import os

    global _disk_cache
    today_str = date.today().strftime("%Y-%m-%d")
    try:
        for f in _disk_cache._cache_dir.glob("*.db"):
            if f.stem != today_str:
                os.unlink(f)
        _disk_cache.close()
        _disk_cache = DiskCache()
    except OSError:
        pass


def _import_sources() -> None:
    from financial_data_query import sources  # noqa: F401
