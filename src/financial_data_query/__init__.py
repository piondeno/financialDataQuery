from datetime import timedelta
from datetime import date as _date
from datetime import datetime as _datetime
import fcntl
import json
import os
import pandas as pd
from financial_data_query.config import load_env
from financial_data_query.registry import Registry
from financial_data_query.cache import QueryCache
from financial_data_query.base import DataSourceFetcher, _filter_by_date
from financial_data_query.disk_cache import DiskCache
from financial_data_query.constants import (
    DATE_FORMAT,
    _DEFAULT_CACHE_SIZE,
    _DAILY_THRESHOLD_DAYS,
    _WEEKLY_THRESHOLD_DAYS,
)

load_env()

_LOG_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "log"))

def _log_cache_miss(source, symbols, start, end, sub_field, frequency):
    """Log cache miss to log/YYYY-MM-DD.log, appending new entries."""
    try:
        os.makedirs(_LOG_DIR, exist_ok=True)
        today = _date.today().strftime(DATE_FORMAT)
        log_path = os.path.join(_LOG_DIR, f"{today}.log")
        now = _datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "time": now,
            "source": source,
            "symbols": symbols,
            "start": start,
            "end": end,
            "sub_field": sub_field,
            "frequency": frequency,
        }
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass

_cache = QueryCache(max_size=_DEFAULT_CACHE_SIZE)
_disk_cache = DiskCache()

_FREQUENCY_AWARE_SOURCES = {"yahoo", "stooq"}


# Attribute names used by fetchers to store their full table / full data in memory.
# Each fetcher subclass uses one of these; the cache system introspects them generically.
_BATCH_CACHE_ATTRS = ('_full_table_cache', '_full_data_cache', '_full_df_cache', '_excel_cache')

def _has_batch_cache(fetcher, source):
    """Check if fetcher has batch caching capability (attr exists AND has value).

    Batch-cache fetchers (e.g., tw_ndc, moea, ici) load all data once into memory,
    then extract per-symbol from that cache. This is more efficient than fetching
    each symbol individually, especially for browser-based sources.

    NOTE: Different from _fetches_full_data. Batch-cache fetchers store data in a
    full-table structure (shared across symbols). _fetches_full_data fetchers store
    per-symbol full data independently. A fetcher can have both (e.g., ici).
    """
    for attr in _BATCH_CACHE_ATTRS:
        val = getattr(fetcher, attr, None)
        if val is not None:
            return True
    return False

def _get_batch_cache(fetcher, source):
    """Check if fetcher has a batch cache and return the full table."""
    for attr in _BATCH_CACHE_ATTRS:
        cache = getattr(fetcher, attr, None)
        if hasattr(cache, 'get'):  # dict-like
            if cache.get(source) is not None:
                return cache[source]
        elif cache is not None and hasattr(cache, 'shape'):  # DataFrame
            return cache
    return None


def _set_batch_cache(fetcher, source, df):
    """Store full table in the fetcher's batch cache."""
    for attr in _BATCH_CACHE_ATTRS:
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
    if days <= _DAILY_THRESHOLD_DAYS:
        return "daily"
    elif days <= _WEEKLY_THRESHOLD_DAYS:
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
                record[k] = v.strftime(DATE_FORMAT)
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

    symbols = symbol if isinstance(symbol, list) else [symbol]
    results = _batch_query(
        fetcher, source, symbols, start, end, sub_field, frequency, output, use_cache, is_single=(not isinstance(symbol, list))
    )
    return results


def _apply_sub_field(df: pd.DataFrame, sub_field: str | None) -> pd.DataFrame:
    if not sub_field or sub_field not in df.columns:
        return df
    return df[[sub_field]]


def _batch_query(
    fetcher, source, symbols, start, end, sub_field, frequency, output, use_cache, is_single=False
):
    """Batch query with 4-tier caching: in-memory LRU → in-memory batch cache → disk cache → live fetch.

    Cache flow:
      1. In-memory LRU cache (process-local, fast but not shared)
      2. In-memory batch cache (process-local, for fetchers that load full tables)
      3. Disk cache full table (cross-process, for batch-cache fetchers)
      4. Disk cache per-symbol (cross-process, for non-batch fetchers)
      5. Live fetch with cross-process lock (prevents concurrent browser opens)
    """
    effective_freq = _auto_frequency(source, start, end, frequency)
    results = {}
    cached_symbols = []

    # Tier 1: In-memory LRU cache (process-local, O(1) lookup)
    if use_cache:
        for s in symbols:
            cached = _cache.get(source, s, start, end, sub_field, effective_freq)
            if cached is not None:
                results[s] = cached
                cached_symbols.append(s)

    to_fetch = [s for s in symbols if s not in cached_symbols]

    disk_hit_symbols = []
    if use_cache and to_fetch:
        # Tier 2: In-memory batch cache (same process, for fetchers that load full tables once)
        # E.g., tw_ndc, moea — these fetch all data into a dict, then extract per-symbol
        if _has_batch_cache(fetcher, source):
            full_table = _get_batch_cache(fetcher, source)
            if full_table is not None:
                for s in to_fetch:
                    # Match exact symbol or "symbol_" prefix (e.g., "化學品_美國")
                    match_cols = [c for c in full_table.columns if c == s or c.startswith(s + "_")]
                    if match_cols:
                        candidate = full_table[match_cols].copy()
                        prefix = s + "_"
                        rename_map = {}
                        for c in match_cols:
                            if c.startswith(prefix):
                                rename_map[c] = c.removeprefix(prefix)
                            elif c == s:
                                rename_map[c] = "value"
                        if rename_map:
                            candidate.rename(columns=rename_map, inplace=True)
                        filtered = _filter_by_date(candidate, start, end)
                        if sub_field and len(filtered.columns) > 1:
                            filtered = _apply_sub_field(filtered, sub_field)
                        if len(filtered):
                            results[s] = filtered
                            disk_hit_symbols.append(s)

        # Tier 3: Disk cache full table (cross-process, for batch-cache fetchers)
        # Stored as "_{source}_full_table" key, shared across processes via SQLite
        for s in to_fetch:
            if s in disk_hit_symbols:
                continue
            disk_df = _disk_cache.get(source, f"_{source}_full_table", frequency=effective_freq)
            if disk_df is not None and len(disk_df):
                # Overlaps check: serve partial data if date ranges overlap
                # (next fetch will merge; avoid rejecting useful cached data)
                overlaps = True
                if start and disk_df.index.max() < pd.Timestamp(start):
                    overlaps = False
                if end and disk_df.index.min() > pd.Timestamp(end):
                    overlaps = False
                if overlaps:
                    filtered = _filter_by_date(disk_df, start, end)
                    # Support both exact match and prefix match for composite columns
                    match_cols = [c for c in filtered.columns if c == s or c.startswith(s + "_")]
                    if match_cols:
                        sub_df = filtered[match_cols].copy()
                        prefix = s + "_"
                        rename_map = {}
                        for c in match_cols:
                            if c.startswith(prefix):
                                rename_map[c] = c.removeprefix(prefix)
                            elif c == s:
                                rename_map[c] = "value"
                        if rename_map:
                            sub_df.rename(columns=rename_map, inplace=True)
                        if sub_field and len(sub_df.columns) > 1:
                            sub_df = _apply_sub_field(sub_df, sub_field)
                        if len(sub_df):
                            results[s] = sub_df
                            disk_hit_symbols.append(s)
                            continue
                    
        # Tier 4: Disk cache per-symbol (cross-process, for non-batch fetchers)
        # E.g., yahoo, fred — each symbol cached independently
        # E.g., macroMicro, multpl, zillow — each symbol cached with FULL data
        for s in to_fetch:
            if s in disk_hit_symbols:
                continue
            # For _fetches_full_data=True: validate _expected_columns to detect API schema changes.
            # If columns don't match, the cached data is stale and we re-fetch.
            # For _fetches_full_data=False: no validation (yahoo/fred merge with existing).
            expected_cols = None
            if getattr(fetcher, '_fetches_full_data', False):
                expected_cols = getattr(fetcher, '_expected_columns', None)
                if expected_cols is None:
                    api_cols = getattr(fetcher, '_API_COLUMNS', None)
                    if api_cols is not None:
                        rename_map = getattr(fetcher, '_COLUMN_RENAME_MAP', {})
                        expected_cols = [rename_map.get(c, c) for c in api_cols]

            disk_df = _disk_cache.get(source, s, frequency=effective_freq, expected_columns=expected_cols)
            if disk_df is not None and len(disk_df):
                overlaps = True
                if start and disk_df.index.max() < pd.Timestamp(start):
                    overlaps = False
                if end and disk_df.index.min() > pd.Timestamp(end):
                    overlaps = False
                if overlaps:
                    filtered = _filter_by_date(disk_df, start, end)
                    if sub_field and len(filtered.columns) > 1:
                        filtered = _apply_sub_field(filtered, sub_field)
                    if len(filtered):
                        results[s] = filtered
                        disk_hit_symbols.append(s)

    # Tier 5: Live fetch with cross-process lock
    still_to_fetch = [s for s in to_fetch if s not in disk_hit_symbols]
    if still_to_fetch:
        _log_cache_miss(source, still_to_fetch, start, end, sub_field, effective_freq)
        lock_fd = None
        try:
            # Cross-process lock: prevents two processes from opening browsers simultaneously
            # for the same source. Lock file lives in the cache directory per source.
            lock_path = _disk_cache._cache_dir / f".lock_{source}"
            lock_fd = open(lock_path, "w")
            fcntl.flock(lock_fd, fcntl.LOCK_EX)

            # Double-check: another process may have fetched while we waited for the lock.
            # Re-read disk cache for:
            #   1) _has_batch_cache: check full table cache (e.g., tw_ndc, moea, ici)
            #   2) _fetches_full_data: check per-symbol cache (e.g., macroMicro, multpl, zillow)
            # For _fetches_full_data: the disk cache holds ALL data, so we can filter by start/end
            # to serve partial results — this prevents unnecessary re-fetches across processes.
            if use_cache and (
                _has_batch_cache(fetcher, source)
                or getattr(fetcher, '_fetches_full_data', False)
            ):
                for s in list(still_to_fetch):
                    if s in results:
                        still_to_fetch.remove(s)
                    # Batch-cache fetchers: check full table cache
                    if _has_batch_cache(fetcher, source):
                        disk_df = _disk_cache.get(source, f"_{source}_full_table", frequency=effective_freq)
                        if disk_df is not None and len(disk_df):
                            overlaps = True
                            if start and disk_df.index.max() < pd.Timestamp(start):
                                overlaps = False
                            if end and disk_df.index.min() > pd.Timestamp(end):
                                overlaps = False
                            if overlaps:
                                filtered = _filter_by_date(disk_df, start, end)
                                match_cols = [c for c in filtered.columns if c == s or c.startswith(s + "_")]
                                if match_cols:
                                    sub_df = filtered[match_cols].copy()
                                    prefix = s + "_"
                                    rename_map = {}
                                    for c in match_cols:
                                        if c.startswith(prefix):
                                            rename_map[c] = c.removeprefix(prefix)
                                        elif c == s:
                                            rename_map[c] = "value"
                                    if rename_map:
                                        sub_df.rename(columns=rename_map, inplace=True)
                                    if sub_field and len(sub_df.columns) > 1:
                                        sub_df = _apply_sub_field(sub_df, sub_field)
                                    if len(sub_df):
                                        results[s] = sub_df
                    # _fetches_full_data fetchers: check per-symbol cache.
                    # The disk cache holds ALL data for this symbol.
                    # We validate _expected_columns to detect API schema changes,
                    # then filter by date range to serve the requested window.
                    elif getattr(fetcher, '_fetches_full_data', False):
                        expected_cols = getattr(fetcher, '_expected_columns', None)
                        if expected_cols is None:
                            api_cols = getattr(fetcher, '_API_COLUMNS', None)
                            if api_cols is not None:
                                rename_map = getattr(fetcher, '_COLUMN_RENAME_MAP', {})
                                expected_cols = [rename_map.get(c, c) for c in api_cols]
                        disk_df = _disk_cache.get(source, s, frequency=effective_freq, expected_columns=expected_cols)
                        if disk_df is not None and len(disk_df):
                            overlaps = True
                            if start and disk_df.index.max() < pd.Timestamp(start):
                                overlaps = False
                            if end and disk_df.index.min() > pd.Timestamp(end):
                                overlaps = False
                            if overlaps:
                                filtered = _filter_by_date(disk_df, start, end)
                                if sub_field and len(filtered.columns) > 1:
                                    filtered = _apply_sub_field(filtered, sub_field)
                                if len(filtered):
                                    results[s] = filtered

            still_to_fetch = [s for s in still_to_fetch if s not in results]

            if still_to_fetch:
                batch = fetcher.batch_fetch(
                    still_to_fetch, start=start, end=end, sub_field=sub_field, frequency=effective_freq
                )

                for s, df in batch.items():
                    filtered = _filter_by_date(df, start, end)
                    if sub_field and len(filtered.columns) > 1:
                        filtered = _apply_sub_field(filtered, sub_field)
                    results[s] = filtered

                # Persist to disk cache after successful fetch
                if use_cache:
                    try:
                        for s in still_to_fetch:
                            fetched_df = batch.get(s)
                            if fetched_df is None:
                                continue
                            # _fetches_full_data: store the full, unfiltered API response.
                            # Cache flow: batch_fetch returns ALL data → disk stores ALL data →
                            # on subsequent reads, query layer filters by start/end.
                            # This is a direct overwrite — the data is already complete, no merge needed.
                            # Contrast with _fetches_full_data=False: fetch filtered data → merge with existing.
                            # Sources: macroMicro, multpl, zillow, optioncharts, finra, ici, usTreasury
                            if getattr(fetcher, '_fetches_full_data', False):
                                _disk_cache.set(source, s, fetched_df, frequency=effective_freq)
                            # Non-batch, non-full: merge with existing (incremental update)
                            elif not _has_batch_cache(fetcher, source):
                                existing = _disk_cache.get(source, s, frequency=effective_freq)
                                if existing is not None and len(existing):
                                    merged = pd.concat([existing, fetched_df])
                                    merged = merged[~merged.index.duplicated(keep="first")]
                                    merged.sort_index(inplace=True)
                                    _disk_cache.set(source, s, merged, frequency=effective_freq)
                                else:
                                    _disk_cache.set(source, s, fetched_df, frequency=effective_freq)

                        # Save full table to disk for batch-cache fetchers (e.g., tw_ndc, moea)
                        if _has_batch_cache(fetcher, source):
                            for attr in _BATCH_CACHE_ATTRS:
                                full_table = getattr(fetcher, attr, None)
                                if full_table is not None and hasattr(full_table, 'get'):
                                    cached_df = full_table.get(source)
                                    if cached_df is not None and len(cached_df):
                                        _disk_cache.set(source, f"_{source}_full_table", cached_df, frequency=effective_freq)
                                        break
                            else:
                                full_table = _get_batch_cache(fetcher, source)
                                if full_table is not None and len(full_table):
                                    _disk_cache.set(source, f"_{source}_full_table", full_table, frequency=effective_freq)
                    except Exception:
                        pass

                # Update in-memory LRU cache for newly fetched data
                if use_cache:
                    for s, df in results.items():
                        if s not in cached_symbols and s not in disk_hit_symbols:
                            _cache.set(
                                source, s, df, start=start, end=end,
                                sub_field=sub_field, frequency=effective_freq
                            )
        finally:
            if lock_fd is not None:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                lock_fd.close()

    if is_single and len(symbols) == 1:
        s = symbols[0]
        if output == "json":
            return {s: _df_to_json(results[s])}
        if output == "dataframe":
            return results[s]
        return {s: results[s]}

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
    today_str = date.today().strftime(DATE_FORMAT)
    try:
        for f in _disk_cache._cache_dir.glob("*.db"):
            os.unlink(f)
        _disk_cache.close()
        _disk_cache = DiskCache()
    except OSError:
        pass


# Known source modules and their fetcher class names.
# Format: source_name -> (module_path, class_name)
# New sources should be added here to enable auto-registration on first use.
_SOURCE_MODULES = {
    # Market data APIs
    "yahoo": ("financial_data_query.sources.yahoo", "YahooFetcher"),
    "fred": ("financial_data_query.sources.fred", "FredFetcher"),
    # Browser-based scrapers (require undetected-chromedriver)
    "stooq": ("financial_data_query.sources.stooq", "StooqFetcher"),
    # Taiwan NDC (browser-based, cross-process lock protected)
    "tw_eco": ("financial_data_query.sources.tw_ndc", "TwEcoFetcher"),
    "tw_pmi": ("financial_data_query.sources.tw_ndc", "TwPmiFetcher"),
    # Taiwan MOEA export data (browser-based)
    "moea": ("financial_data_query.sources.moeab", "MoeaFetcher"),
    # Excel-based downloads
    "finra_margin": ("financial_data_query.sources.finra_margin", "FinraMarginFetcher"),
    "ici": ("financial_data_query.sources.ici", "IciFetcher"),
    # MacroMicro (browser-based, requires symbol URL registration first)
    "macroMicro": ("financial_data_query.sources.macroMicro", "MacroMicroFetcher"),
    # US Treasury API (paginated, full-data fetch)
    "usTreasuryApi": ("financial_data_query.sources.us_treasury", "UsTreasuryFetcher"),
    # Multpl (HTTP scraping)
    "multpl": ("financial_data_query.sources.multpl", "MultplFetcher"),
    # AkShare (China market data)
    "akshare": ("financial_data_query.sources.akshare", "AkShareFetcher"),
    # Zillow real estate data
    "zillow": ("financial_data_query.sources.zillow", "ZillowFetcher"),
    # OptionCharts (options flow)
    "optioncharts": ("financial_data_query.sources.optioncharts", "OptionchartsFetcher"),
    # MQL5 economic calendar
    "mql5": ("financial_data_query.sources.mql5", "Mql5Fetcher"),
}


def _import_sources() -> None:
    from importlib import import_module
    for source_name, (module_name, class_name) in _SOURCE_MODULES.items():
        if source_name in Registry._fetchers:
            continue
        try:
            mod = import_module(module_name)
            fetcher_cls = getattr(mod, class_name)
            Registry.register(fetcher_cls)
        except (ImportError, AttributeError):
            pass
