import pytest
import pandas as pd
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

    def test_fetch_returns_dataframe(self, fetcher):
        csv_content = "Date,Open,High,Low,Close,Volume\n2024-01-01,100,101,99,100.5,1000"
        expected_df = fetcher._parse_csv(csv_content)
        mock_driver = mock.MagicMock()

        with mock.patch.object(fetcher, "_create_driver", return_value=mock_driver):
            with mock.patch.object(fetcher, "_fetch_with_driver", return_value=expected_df):
                result = fetcher.fetch("dx.c")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        mock_driver.quit.assert_called_once()

    def test_fetch_with_frequency(self, fetcher):
        csv_content = "Date,Open,High,Low,Close,Volume\n2024-01-01,100,101,99,100.5,1000"
        expected_df = fetcher._parse_csv(csv_content)
        mock_driver = mock.MagicMock()

        with mock.patch.object(fetcher, "_create_driver", return_value=mock_driver):
            with mock.patch.object(fetcher, "_fetch_with_driver", return_value=expected_df) as m:
                result = fetcher.fetch("dx.c", frequency="1wk")
        assert isinstance(result, pd.DataFrame)
        m.assert_called_once()
        call_kwargs = m.call_args[1]
        assert call_kwargs["frequency"] == "1wk"

    def test_fetch_with_date_range(self, fetcher):
        csv_content = "Date,Open,High,Low,Close,Volume\n2024-06-01,100,101,99,100.5,1000"
        expected_df = fetcher._parse_csv(csv_content)
        mock_driver = mock.MagicMock()

        with mock.patch.object(fetcher, "_create_driver", return_value=mock_driver):
            with mock.patch.object(fetcher, "_fetch_with_driver", return_value=expected_df) as m:
                result = fetcher.fetch("dx.c", start="2024-06-01", end="2024-12-31")
        assert isinstance(result, pd.DataFrame)
        call_kwargs = m.call_args[1]
        assert call_kwargs["start"] == "2024-06-01"
        assert call_kwargs["end"] == "2024-12-31"

    def test_fetch_empty_data_raises(self, fetcher):
        mock_driver = mock.MagicMock()
        with mock.patch.object(fetcher, "_create_driver", return_value=mock_driver):
            with mock.patch.object(fetcher, "_fetch_with_driver", side_effect=FetchError("empty")):
                with pytest.raises(FetchError):
                    fetcher.fetch("INVALID")

    def test_fetch_closes_browser_on_error(self, fetcher):
        mock_driver = mock.MagicMock()
        mock_uc = mock.MagicMock()
        mock_uc.Chrome.return_value = mock_driver

        with mock.patch.object(fetcher, "_create_driver", return_value=mock_driver):
            with mock.patch.object(fetcher, "_fetch_with_driver", side_effect=Exception("Page load failed")):
                with pytest.raises(Exception):
                    fetcher.fetch("dx.c")
        mock_driver.quit.assert_called_once()

    def test_batch_fetch_uses_single_driver(self, fetcher):
        expected_df = fetcher._parse_csv("Date,Open,High,Low,Close,Volume\n2024-01-01,100,101,99,100.5,1000")
        mock_driver = mock.MagicMock()
        call_count = 0

        def fake_create_driver():
            nonlocal call_count
            call_count += 1
            return mock_driver

        with mock.patch.object(fetcher, "_create_driver", side_effect=fake_create_driver):
            with mock.patch.object(fetcher, "_fetch_with_driver", return_value=expected_df) as m:
                results = fetcher.batch_fetch(["A", "B", "C"])
        assert call_count == 1
        assert m.call_count == 3
        assert set(results.keys()) == {"A", "B", "C"}
        mock_driver.quit.assert_called_once()

    def test_fetcher_is_registered(self, fetcher):
        from financial_data_query.registry import Registry
        assert Registry.is_registered("stooq")