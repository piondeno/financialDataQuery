import pytest
import pandas as pd
import io
from unittest import mock
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
