import pytest
import pandas as pd
import io
from unittest import mock
from contextlib import ExitStack
from financial_data_query.sources.stooq import StooqFetcher
from financial_data_query.errors import FetchError


class TestStooqFetcher:
    @pytest.fixture
    def fetcher(self):
        return StooqFetcher()

    def test_source_name(self, fetcher):
        assert fetcher.source_name == "stooq"

    def test_parse_csv_returns_dataframe(self, fetcher):
        csv_content = "Date,Open,High,Low,Close,Volume\n2024-01-01,100,101,99,100.5,1000\n2024-01-02,100.5,102,100,101.5,1200"
        df = fetcher._parse_csv(csv_content)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert isinstance(df.index, pd.DatetimeIndex)
        assert "Close" in df.columns

    def test_frequency_map_contains_all_intervals(self, fetcher):
        assert "1d" in fetcher._FREQUENCY_MAP
        assert "1wk" in fetcher._FREQUENCY_MAP
        assert "1mo" in fetcher._FREQUENCY_MAP
        assert "3mo" in fetcher._FREQUENCY_MAP
        assert "1y" in fetcher._FREQUENCY_MAP

    def test_validate_frequency_valid(self, fetcher):
        for freq in ["1d", "1wk", "1mo", "3mo", "1y"]:
            assert fetcher._validate_frequency(freq) is True

    def test_validate_frequency_invalid_raises(self, fetcher):
        with pytest.raises(FetchError, match="Invalid frequency"):
            fetcher._validate_frequency("5m")

    def _setup_fetch_mocks(self, csv_content, csv_url="https://stooq.com/q/d/l?s=dx.c"):
        mock_driver = mock.MagicMock()
        mock_csv_link = mock.MagicMock()
        mock_csv_link.get_attribute.return_value = csv_url

        mock_uc = mock.MagicMock()
        mock_uc.Chrome.return_value = mock_driver

        mock_requests = mock.MagicMock()
        mock_requests.get.return_value.text = csv_content

        mock_by = mock.MagicMock()
        mock_select = mock.MagicMock()
        mock_wait = mock.MagicMock()
        mock_wait.return_value.until.side_effect = lambda cond: mock_csv_link
        mock_ec = mock.MagicMock()

        patches = [
            mock.patch("financial_data_query.sources.stooq.uc", mock_uc),
            mock.patch("financial_data_query.sources.stooq.requests", mock_requests),
            mock.patch("financial_data_query.sources.stooq.By", mock_by),
            mock.patch("financial_data_query.sources.stooq.Select", mock_select),
            mock.patch("financial_data_query.sources.stooq.WebDriverWait", mock_wait),
            mock.patch("financial_data_query.sources.stooq.EC", mock_ec),
        ]
        return patches, mock_uc, mock_driver, mock_requests

    def test_fetch_returns_dataframe(self, fetcher):
        csv_content = "Date,Open,High,Low,Close,Volume\n2024-01-01,100,101,99,100.5,1000"
        patches, mock_uc, mock_driver, mock_requests = self._setup_fetch_mocks(csv_content)
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            result = fetcher.fetch("dx.c")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        mock_uc.Chrome.assert_called_once()
        mock_driver.quit.assert_called_once()

    def test_fetch_with_frequency(self, fetcher):
        csv_content = "Date,Open,High,Low,Close,Volume\n2024-01-01,100,101,99,100.5,1000"
        patches, mock_uc, mock_driver, mock_requests = self._setup_fetch_mocks(csv_content)
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            result = fetcher.fetch("dx.c", frequency="1wk")
        assert isinstance(result, pd.DataFrame)

    def test_fetch_with_date_range(self, fetcher):
        csv_content = "Date,Open,High,Low,Close,Volume\n2024-06-01,100,101,99,100.5,1000"
        patches, mock_uc, mock_driver, mock_requests = self._setup_fetch_mocks(csv_content)
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            result = fetcher.fetch("dx.c", start="2024-06-01", end="2024-12-31")
        assert isinstance(result, pd.DataFrame)

    def test_fetch_empty_data_raises(self, fetcher):
        csv_content = "Date,Open,High,Low,Close,Volume"
        patches, mock_uc, mock_driver, mock_requests = self._setup_fetch_mocks(csv_content)
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            with pytest.raises(FetchError):
                fetcher.fetch("INVALID")

    def test_fetch_closes_browser_on_error(self, fetcher):
        mock_driver = mock.MagicMock()
        mock_driver.get.side_effect = Exception("Page load failed")
        mock_uc = mock.MagicMock()
        mock_uc.Chrome.return_value = mock_driver

        with mock.patch("financial_data_query.sources.stooq.uc", mock_uc):
            with pytest.raises(Exception):
                fetcher.fetch("dx.c")
        mock_driver.quit.assert_called_once()

    def test_fetcher_is_registered(self, fetcher):
        from financial_data_query.registry import Registry
        assert Registry.is_registered("stooq")