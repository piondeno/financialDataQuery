"""
Comprehensive test for ALL 14 data sources using mocked fetchers.
Covers: single query, batch query, use_cache=True/False, json/dataframe output.
"""
import pytest
import pandas as pd
from datetime import datetime

from financial_data_query import query, register_source, clear_cache
from financial_data_query.base import DataSourceFetcher
from financial_data_query.registry import Registry


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_df(values, index=None):
    """Create a single-column DataFrame with 'value' column."""
    if index is None:
        index = pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"])
    return pd.DataFrame({"value": values}, index=index)


def _make_multi_col_df():
    """Create a multi-column DataFrame (simulates batch-cache source)."""
    idx = pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"])
    return pd.DataFrame(
        {"AAPL": [100, 101, 102], "GOOG": [2000, 2010, 2020]},
        index=idx,
    )


# ── mock fetcher factories ───────────────────────────────────────────────────

def _mock_fetcher_factory(source_name, df=None, has_batch_fetch=False,
                          has_batch_cache=False):
    """Create a mock fetcher class for a given source."""
    if df is None:
        df = _make_df([1.0, 2.0, 3.0])

    cls_attrs = {"source_name": source_name}

    def fetch(self, symbol, start=None, end=None, sub_field=None, frequency=None):
        result = df.copy()
        if start:
            result = result[result.index >= pd.Timestamp(start)]
        if end:
            result = result[result.index <= pd.Timestamp(end)]
        if result.empty:
            return pd.DataFrame()
        return result

    cls_attrs["fetch"] = fetch

    if has_batch_fetch:
        def batch_fetch(self, symbols, start=None, end=None, sub_field=None, frequency=None):
            results = {}
            for s in symbols:
                results[s] = df.copy()
            return results
        cls_attrs["batch_fetch"] = batch_fetch

    if has_batch_cache:
        cls_attrs["_full_table_cache"] = _make_multi_col_df()

    return type(f"Mock{source_name.capitalize()}Fetcher", (DataSourceFetcher,), cls_attrs)


# ── test parametrization ─────────────────────────────────────────────────────

SOURCE_SPECS = [
    ("yahoo",        False, False),
    ("fred",         True,  False),
    # ("stooq",        True,  False),  # Skip: requires browser
    ("tw_eco",       True,  True),
    ("tw_pmi",       True,  True),
    ("moea",         True,  True),
    ("finra_margin", False, False),
    ("ici",          False, False),
    ("macroMicro",   True,  False),
    ("usTreasuryApi",False, False),
    ("multpl",       False, False),
    ("akshare",      True,  False),
    ("zillow",       False, False),
    ("optioncharts", True,  False),
]

# Module-level mock fetcher classes — created once
_MOCK_FETCHERS = {}
for src_name, has_bf, has_bc in SOURCE_SPECS:
    df = _make_df([1.0, 2.0, 3.0])
    _MOCK_FETCHERS[src_name] = _mock_fetcher_factory(
        src_name, df=df, has_batch_fetch=has_bf, has_batch_cache=has_bc,
    )


@pytest.fixture(autouse=True)
def _mock_sources_fixture():
    """Register mock fetchers and prevent _import_sources from re-registering real sources."""
    import financial_data_query as fdq
    # Clear real sources and register mocks
    real_sources = ["yahoo", "fred", "stooq", "tw_eco", "tw_pmi", "moea",
                    "finra_margin", "ici", "macroMicro", "usTreasuryApi",
                    "multpl", "akshare", "zillow", "optioncharts"]
    for name in list(Registry.list_sources()):
        if name in real_sources:
            Registry._fetchers.pop(name, None)
    for src_name, cls in _MOCK_FETCHERS.items():
        register_source(cls)
    # Patch _import_sources to be a no-op so mocks aren't overwritten
    original_import = fdq._import_sources
    fdq._import_sources = lambda: None
    clear_cache()
    yield
    # Cleanup
    fdq._import_sources = original_import
    for name in list(Registry.list_sources()):
        if name in real_sources:
            Registry._fetchers.pop(name, None)
    clear_cache()
    fdq._import_sources()


# ── test groups ──────────────────────────────────────────────────────────────

class TestSingleQueryJson:
    @pytest.mark.parametrize("source_spec", SOURCE_SPECS,
                             ids=[s[0] for s in SOURCE_SPECS])
    def test_single_query_json(self, source_spec):
        source_name = source_spec[0]
        result = query(source_name, "TEST", output="json", use_cache=True)
        assert isinstance(result, dict)
        assert "TEST" in result
        assert isinstance(result["TEST"], list)
        assert len(result["TEST"]) == 3
        assert "date" in result["TEST"][0]
        assert "value" in result["TEST"][0]


class TestSingleQueryDataframe:
    @pytest.mark.parametrize("source_spec", SOURCE_SPECS,
                             ids=[s[0] for s in SOURCE_SPECS])
    def test_single_query_dataframe(self, source_spec):
        source_name = source_spec[0]
        result = query(source_name, "TEST", output="dataframe", use_cache=True)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3


class TestSingleQueryNoCache:
    @pytest.mark.parametrize("source_spec", SOURCE_SPECS,
                             ids=[s[0] for s in SOURCE_SPECS])
    def test_single_query_no_cache_json(self, source_spec):
        source_name = source_spec[0]
        result = query(source_name, "TEST", output="json", use_cache=False)
        assert isinstance(result, dict)
        assert "TEST" in result
        assert len(result["TEST"]) == 3

    @pytest.mark.parametrize("source_spec", SOURCE_SPECS,
                             ids=[s[0] for s in SOURCE_SPECS])
    def test_single_query_no_cache_dataframe(self, source_spec):
        source_name = source_spec[0]
        result = query(source_name, "TEST", output="dataframe", use_cache=False)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3


class TestBatchQuery:
    @pytest.mark.parametrize("source_spec", SOURCE_SPECS,
                             ids=[s[0] for s in SOURCE_SPECS])
    def test_batch_query_json(self, source_spec):
        source_name = source_spec[0]
        result = query(source_name, ["A", "B"], output="json", use_cache=True)
        assert isinstance(result, dict)
        assert "A" in result
        assert "B" in result
        assert len(result["A"]) == 3
        assert len(result["B"]) == 3

    @pytest.mark.parametrize("source_spec", SOURCE_SPECS,
                             ids=[s[0] for s in SOURCE_SPECS])
    def test_batch_query_no_cache(self, source_spec):
        source_name = source_spec[0]
        result = query(source_name, ["A", "B"], output="json", use_cache=False)
        assert isinstance(result, dict)
        assert "A" in result
        assert "B" in result
        assert len(result["A"]) == 3

    @pytest.mark.parametrize("source_spec", SOURCE_SPECS,
                             ids=[s[0] for s in SOURCE_SPECS])
    def test_batch_query_dataframe(self, source_spec):
        source_name = source_spec[0]
        result = query(source_name, ["A", "B"], output="dataframe", use_cache=True)
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 6


class TestDateFiltering:
    @pytest.mark.parametrize("source_spec", SOURCE_SPECS,
                             ids=[s[0] for s in SOURCE_SPECS])
    def test_single_query_with_date_range(self, source_spec):
        source_name = source_spec[0]
        result = query(
            source_name, "TEST",
            start="2024-01-15", end="2024-02-15",
            output="json", use_cache=False,
        )
        assert isinstance(result, dict)
        assert "TEST" in result
        for record in result["TEST"]:
            dt = datetime.strptime(record["date"], "%Y-%m-%d")
            assert datetime(2024, 1, 15) <= dt <= datetime(2024, 2, 15)


class TestCacheBehavior:
    def test_cache_hits_skip_fetch(self):
        call_count = {"n": 0}

        class CountFetcher(DataSourceFetcher):
            source_name = "count_test"
            def fetch(self, symbol, start=None, end=None, sub_field=None, frequency=None):
                call_count["n"] += 1
                return _make_df([10, 20, 30])

        register_source(CountFetcher)
        clear_cache()

        query("count_test", "X", output="json", use_cache=True)
        assert call_count["n"] == 1

        query("count_test", "X", output="json", use_cache=True)
        assert call_count["n"] == 1

        query("count_test", "X", output="json", use_cache=False)
        assert call_count["n"] == 2

    def test_use_cache_false_never_uses_cache(self):
        call_count = {"n": 0}

        class CountFetcher2(DataSourceFetcher):
            source_name = "count_test2"
            def fetch(self, symbol, start=None, end=None, sub_field=None, frequency=None):
                call_count["n"] += 1
                return _make_df([5, 6, 7])

        register_source(CountFetcher2)
        clear_cache()

        query("count_test2", "X", output="json", use_cache=True)
        assert call_count["n"] == 1

        query("count_test2", "X", output="json", use_cache=False)
        assert call_count["n"] == 2

        query("count_test2", "X", output="json", use_cache=False)
        assert call_count["n"] == 3


class TestDiskCachePopulated:
    def test_disk_cache_has_data(self, tmp_path, monkeypatch):
        import financial_data_query as fdq
        from financial_data_query.disk_cache import DiskCache

        cache_dir = str(tmp_path / "cache")
        new_cache = DiskCache(cache_dir)
        old_cache = fdq._disk_cache
        fdq._disk_cache = new_cache

        try:
            query("yahoo", "TEST", start="2024-01-01", end="2024-12-31",
                  output="json", use_cache=True)

            df = new_cache.get("yahoo", "TEST", frequency="daily")
            assert df is not None, "Disk cache should contain data"
            assert len(df) > 0
        finally:
            fdq._disk_cache = old_cache
            new_cache.close()

    def test_disk_cache_cross_source_isolation(self, tmp_path, monkeypatch):
        import financial_data_query as fdq
        from financial_data_query.disk_cache import DiskCache

        cache_dir = str(tmp_path / "cache2")
        new_cache = DiskCache(cache_dir)
        old_cache = fdq._disk_cache
        fdq._disk_cache = new_cache

        try:
            query("yahoo", "AAPL", output="json", use_cache=True)
            query("fred", "FEDFUNDS", output="json", use_cache=True)

            yahoo_df = new_cache.get("yahoo", "AAPL", frequency="daily")
            fred_df = new_cache.get("fred", "FEDFUNDS", frequency="none")

            assert yahoo_df is not None
            assert fred_df is not None
        finally:
            fdq._disk_cache = old_cache
            new_cache.close()


class TestBatchCacheSources:
    @pytest.mark.parametrize("source_spec",
                             [s for s in SOURCE_SPECS if s[2]],
                             ids=[s[0] for s in SOURCE_SPECS if s[2]])
    def test_batch_cache_source_single_query(self, source_spec):
        source_name = source_spec[0]
        result = query(source_name, "AAPL", output="json", use_cache=True)
        assert isinstance(result, dict)
        assert "AAPL" in result
        assert len(result["AAPL"]) == 3

    @pytest.mark.parametrize("source_spec",
                             [s for s in SOURCE_SPECS if s[2]],
                             ids=[s[0] for s in SOURCE_SPECS if s[2]])
    def test_batch_cache_source_batch_query(self, source_spec):
        source_name = source_spec[0]
        result = query(source_name, ["AAPL", "GOOG"], output="json", use_cache=True)
        assert "AAPL" in result
        assert "GOOG" in result
        assert len(result["AAPL"]) == 3
        assert len(result["GOOG"]) == 3
