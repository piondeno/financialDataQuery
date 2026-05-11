import pytest
import pandas as pd
from unittest import mock
from financial_data_query.sources.fred import FredFetcher
from financial_data_query.errors import ConfigError, FetchError


class TestFredFetcher:
    @pytest.fixture
    def fetcher(self):
        return FredFetcher()

    def test_source_name(self, fetcher):
        assert fetcher.source_name == "fred"

    def test_validate_config_missing_key(self, fetcher):
        with mock.patch("financial_data_query.sources.fred.get_config", return_value=None):
            assert fetcher.validate_config() is False

    def test_validate_config_with_key(self, fetcher):
        with mock.patch("financial_data_query.sources.fred.get_config", return_value="abc123"):
            assert fetcher.validate_config() is True

    def test_fetch_without_api_key_raises(self, fetcher):
        with mock.patch("financial_data_query.sources.fred.get_config", return_value=None):
            with pytest.raises(ConfigError):
                fetcher.fetch("GDP")

    def test_fetch_returns_dataframe(self, fetcher):
        mock_response = {
            "observations": [
                ["2024-01-01", "27000.0"],
                ["2024-04-01", "27500.0"],
            ]
        }
        with mock.patch("financial_data_query.sources.fred.get_config", return_value="test_key"):
            with mock.patch("financial_data_query.sources.fred.requests.get") as mock_get:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = mock_response
                result = fetcher.fetch("GDP")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert isinstance(result.index, pd.DatetimeIndex)

    def test_fetch_with_date_range(self, fetcher):
        mock_response = {"observations": [["2024-06-01", "100.0"]]}
        with mock.patch("financial_data_query.sources.fred.get_config", return_value="test_key"):
            with mock.patch("financial_data_query.sources.fred.requests.get") as mock_get:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = mock_response
                fetcher.fetch("GDP", start="2024-06-01", end="2024-12-31")
                call_params = mock_get.call_args[1]["params"]
                assert call_params["sort_order"] == "asc"
                assert call_params["start_date"] == "2024-06-01"
                assert call_params["end_date"] == "2024-12-31"

    def test_fetch_api_error_raises(self, fetcher):
        with mock.patch("financial_data_query.sources.fred.get_config", return_value="test_key"):
            with mock.patch("financial_data_query.sources.fred.requests.get") as mock_get:
                mock_get.return_value.status_code = 403
                with pytest.raises(FetchError):
                    fetcher.fetch("GDP")
