import pytest
import pandas as pd
from financial_data_query import query, register_source, clear_cache
from financial_data_query.base import DataSourceFetcher


class MockFetcher(DataSourceFetcher):
    """Mock fetcher that returns predictable data for testing."""
    source_name = "mock"

    def __init__(self):
        super().__init__()
        self.fetch_calls = []
        self.batch_calls = []

    def fetch(self, symbol, start=None, end=None, sub_field=None, frequency=None):
        self.fetch_calls.append(symbol)
        return pd.DataFrame(
            {"Open": [100.0, 101.0], "Close": [102.0, 103.0]},
            index=pd.to_datetime(["2024-01-01", "2024-01-02"]),
        )

    def batch_fetch(self, symbols, start=None, end=None, sub_field=None, frequency=None):
        self.batch_calls.append(list(symbols))
        results = {}
        for s in symbols:
            results[s] = pd.DataFrame(
                {"Open": [100.0, 101.0], "Close": [102.0, 103.0]},
                index=pd.to_datetime(["2024-01-01", "2024-01-02"]),
            )
        return results


@pytest.fixture(autouse=True)
def cleanup():
    clear_cache()
    yield


@pytest.fixture
def mock_fetcher():
    register_source(MockFetcher)
    f = MockFetcher()
    # Replace the registered instance with our test instance
    from financial_data_query.registry import Registry
    Registry._fetchers["mock"] = f
    return f


class TestSingleQueryJsonOutput:
    def test_single_symbol_returns_json_by_default(self, mock_fetcher):
        result = query("mock", "AAPL")
        assert isinstance(result, dict)
        assert "AAPL" in result
        assert isinstance(result["AAPL"], list)
        assert len(result["AAPL"]) == 2

    def test_json_has_lowercase_keys(self, mock_fetcher):
        result = query("mock", "AAPL")
        record = result["AAPL"][0]
        assert "open" in record
        assert "close" in record
        assert "date" in record

    def test_json_date_is_string(self, mock_fetcher):
        result = query("mock", "AAPL")
        assert isinstance(result["AAPL"][0]["date"], str)

    def test_dataframe_output_returns_dataframe(self, mock_fetcher):
        df = query("mock", "AAPL", output="dataframe")
        assert isinstance(df, pd.DataFrame)
        assert "Open" in df.columns


class TestBatchQueryJsonOutput:
    def test_batch_returns_json_by_default(self, mock_fetcher):
        result = query("mock", ["AAPL", "TSLA"])
        assert isinstance(result, dict)
        assert "AAPL" in result
        assert "TSLA" in result

    def test_batch_calls_batch_fetch_method(self, mock_fetcher):
        query("mock", ["AAPL", "TSLA"])
        assert len(mock_fetcher.batch_calls) == 1
        assert set(mock_fetcher.batch_calls[0]) == {"AAPL", "TSLA"}

    def test_batch_json_format(self, mock_fetcher):
        result = query("mock", ["AAPL", "TSLA"])
        for symbol, records in result.items():
            assert isinstance(records, list)
            for r in records:
                assert "date" in r
                assert "open" in r

    def test_batch_dataframe_output(self, mock_fetcher):
        df = query("mock", ["AAPL", "TSLA"], output="dataframe")
        assert isinstance(df, pd.DataFrame)
        assert "Symbol" in df.columns
        assert set(df["Symbol"].unique()) == {"AAPL", "TSLA"}


class TestErrorPropagation:
    def test_batch_error_aborts_all(self):
        class FailingFetcher(DataSourceFetcher):
            source_name = "failing"

            def fetch(self, symbol, start=None, end=None, sub_field=None, frequency=None):
                raise RuntimeError("fail")

            def batch_fetch(self, symbols, start=None, end=None, sub_field=None, frequency=None):
                raise RuntimeError("fail")

        register_source(FailingFetcher)
        with pytest.raises(Exception):
            query("failing", ["A", "B"])


class TestBatchCaching:
    def test_cached_symbols_not_fetched_again(self, mock_fetcher):
        query("mock", "AAPL")
        mock_fetcher.batch_calls.clear()
        mock_fetcher.fetch_calls.clear()

        result = query("mock", ["AAPL", "TSLA"])
        assert "AAPL" in result
        assert "TSLA" in result
        assert "TSLA" in mock_fetcher.batch_calls[0]
        assert "AAPL" not in mock_fetcher.batch_calls[0]
