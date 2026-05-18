import pytest
import pandas as pd
from financial_data_query import query, register_source, list_sources
from financial_data_query.base import DataSourceFetcher
from financial_data_query.errors import DataSourceNotFoundError


class DummyFetcher(DataSourceFetcher):
    source_name = "dummy"

    def fetch(self, symbol, start=None, end=None, sub_field=None, frequency=None):
        return pd.DataFrame(
            {"value": [42.0]},
            index=pd.to_datetime(["2024-01-01"]),
        )


def test_list_sources_includes_builtins():
    sources = list_sources()
    assert "yahoo" in sources
    assert "fred" in sources


def test_query_with_dummy_source():
    register_source(DummyFetcher)
    result = query("dummy", "TEST")
    assert isinstance(result, dict)
    assert "TEST" in result
    assert result["TEST"][0]["value"] == 42.0


def test_query_unregistered_source_raises():
    with pytest.raises(DataSourceNotFoundError):
        query("nonexistent_xyz", "TEST")


def test_query_uses_cache():
    call_count = 0

    class CountingFetcher(DataSourceFetcher):
        source_name = "counting"

        def fetch(self, symbol, start=None, end=None, sub_field=None, frequency=None):
            nonlocal call_count
            call_count += 1
            return pd.DataFrame(
                {"value": [1.0]},
                index=pd.to_datetime(["2024-01-01"]),
            )

    register_source(CountingFetcher)
    query("counting", "A", output="dataframe")
    query("counting", "A", output="dataframe")
    assert call_count == 1, "Second call should hit cache"

    query("counting", "A", output="dataframe", use_cache=False)
    assert call_count == 2, "use_cache=False should bypass cache"


def test_query_frequency_different_cache_entries():
    call_count = 0

    class FreqCountingFetcher(DataSourceFetcher):
        source_name = "freqcount"

        def fetch(self, symbol, start=None, end=None, sub_field=None, frequency=None):
            nonlocal call_count
            call_count += 1
            return pd.DataFrame(
                {"value": [1.0]},
                index=pd.to_datetime(["2024-01-01"]),
            )

    register_source(FreqCountingFetcher)
    query("freqcount", "A", frequency="daily", output="dataframe")
    query("freqcount", "A", frequency="weekly", output="dataframe")
    assert call_count == 2, "Different frequencies should not share cache"

    query("freqcount", "A", frequency="daily", output="dataframe")
    assert call_count == 2, "Same frequency should hit cache"
