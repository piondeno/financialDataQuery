import pytest
import pandas as pd
from financial_data_query import query, register_source, list_sources
from financial_data_query.base import DataSourceFetcher
from financial_data_query.errors import DataSourceNotFoundError


class DummyFetcher(DataSourceFetcher):
    source_name = "dummy"

    def fetch(self, symbol, start=None, end=None, sub_field=None):
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
    df = query("dummy", "TEST")
    assert isinstance(df, pd.DataFrame)
    assert df.iloc[0]["value"] == 42.0


def test_query_unregistered_source_raises():
    with pytest.raises(DataSourceNotFoundError):
        query("nonexistent_xyz", "TEST")


def test_query_uses_cache():
    call_count = 0

    class CountingFetcher(DataSourceFetcher):
        source_name = "counting"

        def fetch(self, symbol, start=None, end=None, sub_field=None):
            nonlocal call_count
            call_count += 1
            return pd.DataFrame(
                {"value": [1.0]},
                index=pd.to_datetime(["2024-01-01"]),
            )

    register_source(CountingFetcher)
    query("counting", "A")
    query("counting", "A")
    assert call_count == 1, "Second call should hit cache"

    query("counting", "A", use_cache=False)
    assert call_count == 2, "use_cache=False should bypass cache"
