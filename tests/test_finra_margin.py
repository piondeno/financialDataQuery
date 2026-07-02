import os
import pandas as pd
import pytest
from unittest import mock
from financial_data_query.sources.finra_margin import FinraMarginFetcher
from financial_data_query.errors import FetchError


class TestFinraMarginFetcher:
    @pytest.fixture
    def fetcher(self):
        return FinraMarginFetcher()

    def _create_mock_df(self):
        """Create a mock DataFrame matching _get_full_df's output format."""
        df = pd.DataFrame({
            "Year-Month": pd.to_datetime(["2024-01", "2024-02", "2024-03", "2024-04"])
            + pd.offsets.MonthEnd(0),
            "Debit Balances in Customers' Securities Margin Accounts": [1000, 1100, 1050, 1200],
            "Free Credit Balances in Customers' Cash Accounts": [500, 520, 480, 530],
            "Free Credit Balances in Customers' Securities Margin Accounts": [300, 310, 290, 320],
        })
        df.set_index("Year-Month", inplace=True)
        return df

    def test_source_name(self, fetcher):
        assert fetcher.source_name == "finra_margin"

    def test_fetch_invalid_symbol_raises(self, fetcher):
        with pytest.raises(FetchError, match="Invalid symbol"):
            fetcher.fetch("invalid_symbol")

    def test_fetch_valid_symbol_returns_dataframe(self, fetcher):
        mock_df = self._create_mock_df()
        fetcher._full_df_cache = mock_df
        fetcher._tmp_path_cache = "/tmp/margin-statistics-test.xlsx"

        result = fetcher.fetch("debit_balances")

        assert isinstance(result, pd.DataFrame)
        assert "value" in result.columns
        assert len(result) == 4
        assert list(result["value"]) == [1000, 1100, 1050, 1200]
        assert isinstance(result.index, pd.DatetimeIndex)

    def test_fetch_free_credit_cash(self, fetcher):
        mock_df = self._create_mock_df()
        fetcher._full_df_cache = mock_df
        fetcher._tmp_path_cache = "/tmp/margin-statistics-test.xlsx"

        result = fetcher.fetch("free_credit_cash")

        assert list(result["value"]) == [500, 520, 480, 530]

    def test_fetch_free_credit_margin(self, fetcher):
        mock_df = self._create_mock_df()
        fetcher._full_df_cache = mock_df
        fetcher._tmp_path_cache = "/tmp/margin-statistics-test.xlsx"

        result = fetcher.fetch("free_credit_margin")

        assert list(result["value"]) == [300, 310, 290, 320]

    def test_fetch_ignores_date_filter(self, fetcher):
        """FINRA returns full data regardless of start/end (fetches_full_data=True)."""
        mock_df = self._create_mock_df()
        fetcher._full_df_cache = mock_df
        fetcher._tmp_path_cache = "/tmp/margin-statistics-test.xlsx"

        result = fetcher.fetch("debit_balances", start="2024-02", end="2024-03")

        # Returns all 4 rows, ignoring start/end
        assert len(result) == 4
        assert list(result["value"]) == [1000, 1100, 1050, 1200]

    def test_fetch_empty_range_no_error(self, fetcher):
        """FINRA returns full data even for future date ranges (ignores start/end)."""
        mock_df = self._create_mock_df()
        fetcher._full_df_cache = mock_df
        fetcher._tmp_path_cache = "/tmp/margin-statistics-test.xlsx"

        result = fetcher.fetch("debit_balances", start="2025-01", end="2025-12")

        assert len(result) == 4

    def test_temp_file_cleaned_up(self, fetcher, tmp_path):
        mock_df = self._create_mock_df()
        excel_path = str(tmp_path / "margin-statistics-test.xlsx")
        mock_df.to_excel(excel_path)
        fetcher._full_df_cache = mock_df
        fetcher._tmp_path_cache = excel_path

        fetcher.fetch("debit_balances")

        assert not os.path.exists(excel_path)

    def test_download_failure_raises(self, fetcher):
        with mock.patch.object(fetcher, "_get_full_df", side_effect=FetchError("download failed")):
            with pytest.raises(FetchError):
                fetcher.fetch("debit_balances")

    def test_cleanup_on_parse_error(self, fetcher, tmp_path):
        excel_path = str(tmp_path / "margin-statistics-test.xlsx")
        mock_df = self._create_mock_df()
        mock_df.to_excel(excel_path)
        fetcher._tmp_path_cache = excel_path

        with mock.patch.object(fetcher, "_get_full_df", side_effect=FetchError("parse error")):
            with pytest.raises(FetchError):
                fetcher.fetch("debit_balances")

        assert not os.path.exists(excel_path)
