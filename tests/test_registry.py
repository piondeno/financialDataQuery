import pytest
import pandas as pd
from financial_data_query.registry import Registry
from financial_data_query.base import DataSourceFetcher
from financial_data_query.errors import DataSourceNotFoundError


class MockFetcher(DataSourceFetcher):
    source_name = "mock"

    def fetch(self, symbol, start=None, end=None, sub_field=None):
        return pd.DataFrame({"value": [1]}, index=pd.to_datetime(["2024-01-01"]))


def test_register_and_get():
    Registry.register(MockFetcher)
    fetcher = Registry.get("mock")
    assert isinstance(fetcher, MockFetcher)


def test_get_unregistered_raises():
    try:
        Registry.get("nonexistent_source_xyz")
        assert False, "Should have raised"
    except DataSourceNotFoundError as e:
        assert "nonexistent_source_xyz" in str(e)


def test_register_returns_singleton_instance():
    Registry.register(MockFetcher)
    f1 = Registry.get("mock")
    f2 = Registry.get("mock")
    assert f1 is f2
