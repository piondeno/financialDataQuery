import pytest
import pandas as pd
from unittest import mock
from financial_data_query.sources.yahoo import YahooFetcher


class TestYahooFetcher:
    @pytest.fixture
    def fetcher(self):
        return YahooFetcher()

    def test_source_name(self, fetcher):
        assert fetcher.source_name == "yahoo"

    def test_validate_config_always_true(self, fetcher):
        assert fetcher.validate_config() is True

    def test_fetch_returns_dataframe(self, fetcher):
        mock_df = pd.DataFrame(
            {"Close": [150.0, 151.0]},
            index=pd.to_datetime(["2024-01-01", "2024-01-02"]),
        )
        with mock.patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value.history.return_value = mock_df
            result = fetcher.fetch("AAPL")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    def test_fetch_with_date_range(self, fetcher):
        mock_df = pd.DataFrame(
            {"Close": [150.0]},
            index=pd.to_datetime(["2024-06-01"]),
        )
        with mock.patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value.history.return_value = mock_df
            fetcher.fetch("AAPL", start="2024-06-01", end="2024-06-30")
            MockTicker.return_value.history.assert_called_once_with(
                start="2024-06-01", end="2024-06-30"
            )

    def test_fetch_with_sub_field(self, fetcher):
        mock_df = pd.DataFrame(
            {"Open": [149.0], "Close": [150.0], "Volume": [1000]},
            index=pd.to_datetime(["2024-01-01"]),
        )
        with mock.patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value.history.return_value = mock_df
            result = fetcher.fetch("AAPL", sub_field="open")
        assert list(result.columns) == ["Open"]

    def test_fetch_empty_result_raises(self, fetcher):
        empty_df = pd.DataFrame()
        with mock.patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value.history.return_value = empty_df
            with pytest.raises(Exception):
                fetcher.fetch("INVALID_SYMBOL")
