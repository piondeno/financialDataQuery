import pytest
import pandas as pd
from unittest import mock
from financial_data_query.sources.yahoo import YahooFetcher
from financial_data_query.errors import FetchError


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
            with pytest.raises(FetchError):
                fetcher.fetch("INVALID_SYMBOL")

    def test_fetch_frequency_weekly(self, fetcher):
        mock_df = pd.DataFrame(
            {"Close": [150.0, 152.0]},
            index=pd.to_datetime(["2024-01-05", "2024-01-12"]),
        )
        with mock.patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value.history.return_value = mock_df
            fetcher.fetch("AAPL", frequency="weekly")
            MockTicker.return_value.history.assert_called_once_with(interval="1wk")

    def test_fetch_frequency_monthly(self, fetcher):
        mock_df = pd.DataFrame(
            {"Close": [150.0, 155.0]},
            index=pd.to_datetime(["2024-01-31", "2024-02-29"]),
        )
        with mock.patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value.history.return_value = mock_df
            fetcher.fetch("AAPL", frequency="monthly")
            MockTicker.return_value.history.assert_called_once_with(interval="1mo")

    def test_fetch_frequency_daily(self, fetcher):
        mock_df = pd.DataFrame(
            {"Close": [150.0]},
            index=pd.to_datetime(["2024-01-01"]),
        )
        with mock.patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value.history.return_value = mock_df
            fetcher.fetch("AAPL", frequency="daily")
            MockTicker.return_value.history.assert_called_once_with(interval="1d")

    def test_fetch_frequency_invalid_raises(self, fetcher):
        mock_df = pd.DataFrame(
            {"Close": [150.0]},
            index=pd.to_datetime(["2024-01-01"]),
        )
        with mock.patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value.history.return_value = mock_df
            with pytest.raises(FetchError, match="Invalid frequency"):
                fetcher.fetch("AAPL", frequency="hourly")

    def test_fetch_frequency_daily_no_change(self, fetcher):
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        mock_df = pd.DataFrame(
            {
                "Open": range(5),
                "High": range(5, 10),
                "Low": range(10, 15),
                "Close": range(15, 20),
                "Volume": range(100, 105),
            },
            index=dates,
        )
        with mock.patch("yfinance.Ticker") as MockTicker:
            MockTicker.return_value.history.return_value = mock_df
            result = fetcher.fetch("AAPL", frequency="daily")
        assert len(result) == 5
