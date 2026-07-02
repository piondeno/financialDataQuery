"""Comprehensive test for today's changes: _fetches_full_data flag, disk cache merge, and source-specific fixes."""
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
import json
import os
import sys
from importlib import reload

from financial_data_query.disk_cache import DiskCache
from financial_data_query.errors import FetchError


class TestFetchesFullDataFlag:
    """Test that _fetches_full_data flag is set correctly on all sources."""

    def test_multpl_has_flag(self):
        from financial_data_query.sources.multpl import MultplFetcher
        assert getattr(MultplFetcher, '_fetches_full_data', False) is True

    def test_zillow_has_flag(self):
        from financial_data_query.sources.zillow import ZillowFetcher
        assert getattr(ZillowFetcher, '_fetches_full_data', False) is True

    def test_optioncharts_has_flag(self):
        from financial_data_query.sources.optioncharts import OptionchartsFetcher
        assert getattr(OptionchartsFetcher, '_fetches_full_data', False) is True

    def test_finra_margin_has_flag(self):
        from financial_data_query.sources.finra_margin import FinraMarginFetcher
        assert getattr(FinraMarginFetcher, '_fetches_full_data', False) is True

    def test_ici_has_flag(self):
        from financial_data_query.sources.ici import IciFetcher
        assert getattr(IciFetcher, '_fetches_full_data', False) is True

    def test_us_treasury_has_flag(self):
        from financial_data_query.sources.us_treasury import UsTreasuryFetcher
        assert getattr(UsTreasuryFetcher, '_fetches_full_data', False) is True

    def test_macro_micro_has_flag(self):
        from financial_data_query.sources.macroMicro import MacroMicroFetcher
        assert getattr(MacroMicroFetcher, '_fetches_full_data', False) is True

    def test_yahoo_no_flag(self):
        from financial_data_query.sources.yahoo import YahooFetcher
        assert getattr(YahooFetcher, '_fetches_full_data', False) is not True

    def test_fred_no_flag(self):
        from financial_data_query.sources.fred import FredFetcher
        assert getattr(FredFetcher, '_fetches_full_data', False) is not True

    def test_stooq_no_flag(self):
        from financial_data_query.sources.stooq import StooqFetcher
        assert getattr(StooqFetcher, '_fetches_full_data', False) is not True

    def test_akshare_no_flag(self):
        from financial_data_query.sources.akshare import AkShareFetcher
        assert getattr(AkShareFetcher, '_fetches_full_data', False) is not True


class TestFetchesFullDataStoresFullData:
    """Test that _fetches_full_data=True sources store unfiltered data to disk."""

    @pytest.fixture
    def tmp_cache_dir(self, tmp_path):
        from financial_data_query import _disk_cache, clear_cache
        import financial_data_query as fdq
        old_cache = _disk_cache
        new_cache = DiskCache(str(tmp_path))
        fdq._disk_cache = new_cache
        yield tmp_path, new_cache
        fdq._disk_cache = old_cache
        new_cache.close()

    def _mock_full_data_fetcher(self, df):
        """Create a fetcher that returns full data with _fetches_full_data=True."""
        fetcher = MagicMock()
        fetcher.source_name = "full_data_source"
        fetcher._fetches_full_data = True
        fetcher.fetch.return_value = df
        fetcher.batch_fetch.return_value = {"TEST": df}
        return fetcher

    def test_stores_unfiltered_data(self, tmp_cache_dir):
        """For _fetches_full_data=True, disk should store ALL data, not just the queried range."""
        from financial_data_query import _disk_cache, clear_cache
        import financial_data_query as fdq

        # Fetcher returns 12 months of data
        full_df = pd.DataFrame(
            {"value": list(range(1, 13))},
            index=pd.date_range("2023-01-01", periods=12, freq="ME"),
        )

        with patch("financial_data_query.Registry.get") as mock_get:
            fetcher = self._mock_full_data_fetcher(full_df)
            mock_get.return_value = fetcher

            clear_cache()

            # Query only 3 months (April-June)
            result = fdq.query(
                "full_data_source",
                "TEST",
                start="2023-04-01",
                end="2023-06-30",
                output="dataframe",
            )

            # Result should only contain requested range
            assert len(result) == 3

        # But disk cache should store ALL 12 months
        disk_result = _disk_cache.get("full_data_source", "TEST", frequency="none")
        assert disk_result is not None
        assert len(disk_result) == 12
        assert disk_result.index.min() == pd.Timestamp("2023-01-31")
        assert disk_result.index.max() == pd.Timestamp("2023-12-31")

    def test_stores_unfiltered_data_different_frequency(self, tmp_cache_dir):
        """Test _fetches_full_data with different frequencies go to different tables."""
        from financial_data_query import _disk_cache, clear_cache
        import financial_data_query as fdq

        daily_df = pd.DataFrame(
            {"value": list(range(1, 31))},
            index=pd.date_range("2023-01-01", periods=30, freq="D"),
        )
        weekly_df = pd.DataFrame(
            {"value": list(range(1, 9))},
            index=pd.date_range("2023-01-01", periods=8, freq="W"),
        )

        with patch("financial_data_query.Registry.get") as mock_get:
            fetcher_daily = self._mock_full_data_fetcher(daily_df)
            mock_get.return_value = fetcher_daily

            clear_cache()
            fdq.query("full_data_source", "TEST", start="2023-01-01", end="2023-01-05",
                      frequency="daily", output="dataframe")

        with patch("financial_data_query.Registry.get") as mock_get:
            fetcher_weekly = self._mock_full_data_fetcher(weekly_df)
            mock_get.return_value = fetcher_weekly

            fdq.query("full_data_source", "TEST", start="2023-01-01", end="2023-01-08",
                      frequency="weekly", output="dataframe")

        # Both should store full data
        daily_result = _disk_cache.get("full_data_source", "TEST", frequency="daily")
        weekly_result = _disk_cache.get("full_data_source", "TEST", frequency="weekly")

        assert daily_result is not None and len(daily_result) == 30
        assert weekly_result is not None and len(weekly_result) == 8


class TestNoFetchesFullDataMerges:
    """Test that _fetches_full_data=False sources merge with existing disk data."""

    @pytest.fixture
    def tmp_cache_dir(self, tmp_path):
        from financial_data_query import _disk_cache, clear_cache
        import financial_data_query as fdq
        old_cache = _disk_cache
        new_cache = DiskCache(str(tmp_path))
        fdq._disk_cache = new_cache
        yield tmp_path, new_cache
        fdq._disk_cache = old_cache
        new_cache.close()

    def _mock_partial_fetcher(self, df):
        """Create a fetcher that returns filtered data (no _fetches_full_data)."""
        fetcher = MagicMock()
        fetcher.source_name = "partial_source"
        fetcher._fetches_full_data = False
        # Explicitly set batch cache attrs to None to avoid MagicMock returning truthy
        fetcher._excel_cache = None
        fetcher._full_table_cache = None
        fetcher._full_data_cache = None
        fetcher._full_df_cache = None
        fetcher.fetch.return_value = df
        fetcher.batch_fetch.return_value = {"TEST": df}
        return fetcher

    def test_merge_increases_data(self, tmp_cache_dir):
        """Second query should merge with existing data, not replace it."""
        from financial_data_query import _disk_cache, clear_cache
        import financial_data_query as fdq

        # First query: Jan-Mar
        q1_df = pd.DataFrame(
            {"value": [1, 2, 3]},
            index=pd.date_range("2023-01-01", periods=3, freq="ME"),
        )

        with patch("financial_data_query.Registry.get") as mock_get:
            fetcher = self._mock_partial_fetcher(q1_df)
            mock_get.return_value = fetcher

            clear_cache()
            fdq.query("partial_source", "TEST", start="2023-01-01", end="2023-03-31",
                      output="dataframe")

        # Disk should have 3 months
        disk_result = _disk_cache.get("partial_source", "TEST", frequency="none")
        assert disk_result is not None and len(disk_result) == 3

        # Second query: Apr-Jun (different range)
        q2_df = pd.DataFrame(
            {"value": [4, 5, 6]},
            index=pd.date_range("2023-04-01", periods=3, freq="ME"),
        )

        with patch("financial_data_query.Registry.get") as mock_get:
            fetcher = self._mock_partial_fetcher(q2_df)
            mock_get.return_value = fetcher

            fdq.query("partial_source", "TEST", start="2023-04-01", end="2023-06-30",
                      output="dataframe")

        # Disk should now have 6 months (merged)
        disk_result = _disk_cache.get("partial_source", "TEST", frequency="none")
        assert disk_result is not None and len(disk_result) == 6

    def test_different_frequency_no_merge(self, tmp_cache_dir):
        """Different frequency should NOT merge - they go to separate tables."""
        from financial_data_query import _disk_cache, clear_cache
        import financial_data_query as fdq

        daily_df = pd.DataFrame(
            {"value": [1, 2, 3]},
            index=pd.date_range("2023-01-01", periods=3, freq="D"),
        )

        with patch("financial_data_query.Registry.get") as mock_get:
            fetcher = self._mock_partial_fetcher(daily_df)
            mock_get.return_value = fetcher

            clear_cache()
            fdq.query("partial_source", "TEST", start="2023-01-01", end="2023-01-03",
                      frequency="daily", output="dataframe")

        weekly_df = pd.DataFrame(
            {"value": [10, 20]},
            index=pd.date_range("2023-01-01", periods=2, freq="W"),
        )

        with patch("financial_data_query.Registry.get") as mock_get:
            fetcher = self._mock_partial_fetcher(weekly_df)
            mock_get.return_value = fetcher

            fdq.query("partial_source", "TEST", start="2023-01-01", end="2023-01-15",
                      frequency="weekly", output="dataframe")

        # Daily should only have 3 rows, weekly should only have 2 rows
        daily_result = _disk_cache.get("partial_source", "TEST", frequency="daily")
        weekly_result = _disk_cache.get("partial_source", "TEST", frequency="weekly")

        assert daily_result is not None and len(daily_result) == 3
        assert weekly_result is not None and len(weekly_result) == 2

    def test_overlap_dedup(self, tmp_cache_dir):
        """Overlapping query should deduplicate, not double the data."""
        from financial_data_query import _disk_cache, clear_cache
        import financial_data_query as fdq

        # First query: Jan-Jun
        df1 = pd.DataFrame(
            {"value": list(range(1, 7))},
            index=pd.date_range("2023-01-01", periods=6, freq="ME"),
        )

        with patch("financial_data_query.Registry.get") as mock_get:
            fetcher = self._mock_partial_fetcher(df1)
            mock_get.return_value = fetcher

            clear_cache()
            fdq.query("partial_source", "TEST", start="2023-01-01", end="2023-06-30",
                      output="dataframe")

        # Second query: Jul-Dec (non-overlapping, triggers fetch + merge)
        df2 = pd.DataFrame(
            {"value": list(range(7, 13))},
            index=pd.date_range("2023-07-01", periods=6, freq="ME"),
        )

        with patch("financial_data_query.Registry.get") as mock_get:
            fetcher = self._mock_partial_fetcher(df2)
            mock_get.return_value = fetcher

            fdq.query("partial_source", "TEST", start="2023-07-01", end="2023-12-31",
                      output="dataframe")

        # Should have 12 months total (Jan-Dec), merged from two queries
        disk_result = _disk_cache.get("partial_source", "TEST", frequency="none")
        assert disk_result is not None and len(disk_result) == 12


class TestUsTreasuryApiFields:
    """Test that usTreasuryApi includes all new primary dealer fields."""

    def test_api_columns_include_primary_dealer(self):
        from financial_data_query.sources.us_treasury import _API_COLUMNS
        assert "primary_dealer_tendered" in _API_COLUMNS
        assert "primary_dealer_accepted" in _API_COLUMNS

    def test_api_columns_include_comp_noncomp(self):
        from financial_data_query.sources.us_treasury import _API_COLUMNS
        assert "comp_accepted" in _API_COLUMNS
        assert "comp_tendered" in _API_COLUMNS
        assert "noncomp_accepted" in _API_COLUMNS

    def test_api_columns_include_bidder(self):
        from financial_data_query.sources.us_treasury import _API_COLUMNS
        assert "direct_bidder_tendered" in _API_COLUMNS
        assert "direct_bidder_accepted" in _API_COLUMNS
        assert "indirect_bidder_tendered" in _API_COLUMNS
        assert "indirect_bidder_accepted" in _API_COLUMNS

    def test_api_columns_include_soma_fima(self):
        from financial_data_query.sources.us_treasury import _API_COLUMNS
        assert "soma_tendered" in _API_COLUMNS
        assert "soma_accepted" in _API_COLUMNS
        assert "fima_noncomp_tendered" in _API_COLUMNS
        assert "fima_noncomp_accepted" in _API_COLUMNS

    def test_api_columns_include_retail(self):
        from financial_data_query.sources.us_treasury import _API_COLUMNS
        assert "treas_retail_tenders_accepted" in _API_COLUMNS
        assert "treas_retail_accepted" in _API_COLUMNS

    def test_api_columns_include_tenders(self):
        from financial_data_query.sources.us_treasury import _API_COLUMNS
        assert "comp_tenders_accepted" in _API_COLUMNS
        assert "noncomp_tenders_accepted" in _API_COLUMNS

    def test_fetch_does_not_filter_by_date(self):
        """usTreasuryApi fetch should NOT filter by start/end (full data)."""
        from financial_data_query.sources.us_treasury import UsTreasuryFetcher

        mock_df = pd.DataFrame({
            "security_term": ["10-Year", "10-Year", "10-Year"],
            "issue_date": pd.to_datetime(["2023-01-01", "2023-06-01", "2024-01-01"]),
        })

        with patch.object(UsTreasuryFetcher, '_get_full_dataframe', return_value=mock_df):
            fetcher = UsTreasuryFetcher()
            result = fetcher.fetch("note_10y", start="2023-06-01", end="2023-06-30")

            # Should return ALL data for 10-Year, not filtered by date
            assert len(result) == 3


class TestMultplRegexFix:
    """Test that multpl correctly handles unicode space (U+2002)."""

    def test_strip_unicode_space(self):
        """Test that U+2002 is removed from value strings."""
        df = pd.DataFrame({
            "date": ["2024-01-01", "2024-02-01"],
            "value": ["1,234\u2002.56", "567\u2002.89"],
        })
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)

        value_str = df["value"].astype(str).str.replace(",", "").str.strip()
        value_str = value_str.str.replace("\u2002", "", regex=False)
        result = pd.to_numeric(value_str, errors="coerce")

        assert result.iloc[0] == pytest.approx(1234.56)
        assert result.iloc[1] == pytest.approx(567.89)

    def test_strip_dagger(self):
        """Test that dagger symbol is removed from value strings."""
        df = pd.DataFrame({
            "date": ["2024-01-01"],
            "value": ["123.45†"],
        })
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)

        value_str = df["value"].astype(str).str.replace(",", "").str.strip()
        value_str = value_str.str.replace("\u2002", "", regex=False)
        value_str = value_str.str.replace("†", "", regex=False)
        result = pd.to_numeric(value_str, errors="coerce")

        assert result.iloc[0] == pytest.approx(123.45)


class TestFinraMarginNoDateFilter:
    """Test that finra_margin fetch does NOT filter by start/end."""

    def test_returns_all_data(self):
        """finra_margin fetch should return all data, not filtered."""
        from financial_data_query.sources.finra_margin import FinraMarginFetcher

        mock_df = pd.DataFrame({
            "Debit Balances in Customers' Securities Margin Accounts": [100, 200, 300],
        }, index=pd.to_datetime(["2023-01-31", "2023-02-28", "2023-03-31"]))

        with patch.object(FinraMarginFetcher, '_get_full_df', return_value=mock_df):
            fetcher = FinraMarginFetcher()
            result = fetcher.fetch("debit_balances", start="2023-02-01", end="2023-02-28")

            # Should return ALL 3 months, not just Feb
            assert len(result) == 3
            assert result["value"].iloc[0] == 100


class TestIciNoDateFilter:
    """Test that ici fetch does NOT filter by start/end."""

    def test_returns_all_data(self):
        """ici fetch should return all data, not filtered."""
        from financial_data_query.sources.ici import IciFetcher

        mock_df_raw = pd.DataFrame(
            [[None] * 10 for _ in range(20)],
            columns=range(10),
        )
        # Set up headers at rows 4, 5, 6
        mock_df_raw.iloc[4, 1] = "Total"
        mock_df_raw.iloc[5, 1] = "long-term"
        mock_df_raw.iloc[6, 1] = ""
        # Set dates at column 0, rows 7+
        dates = pd.date_range("2023-01-01", periods=12, freq="ME").strftime("%m/%d/%Y").tolist()
        for i, d in enumerate(dates):
            mock_df_raw.iloc[7 + i, 0] = d
        # Set values
        for i in range(12):
            mock_df_raw.iloc[7 + i, 1] = 100 + i

        with patch.object(IciFetcher, '_get_parsed_df', return_value=mock_df_raw):
            fetcher = IciFetcher()
            result = fetcher.fetch("mf_total", start="2023-06-01", end="2023-06-30")

            # Should return ALL 12 months, not just June
            assert len(result) == 12


class TestImportSources:
    """Test that _import_sources correctly registers all fetchers."""

    def test_all_sources_registered(self):
        from financial_data_query import Registry, _import_sources
        from financial_data_query import _SOURCE_MODULES

        _import_sources()

        for source_name in _SOURCE_MODULES:
            assert source_name in Registry._fetchers, f"{source_name} not registered"

    def test_source_modules_dict(self):
        from financial_data_query import _SOURCE_MODULES

        expected_sources = [
            "yahoo", "fred", "stooq", "tw_eco", "tw_pmi", "moea",
            "finra_margin", "ici", "macroMicro", "usTreasuryApi",
            "multpl", "akshare", "zillow", "optioncharts",
        ]

        for source in expected_sources:
            assert source in _SOURCE_MODULES, f"{source} missing from _SOURCE_MODULES"


class TestBatchCacheAttrs:
    """Test that _BATCH_CACHE_ATTRS includes _excel_cache."""

    def test_excel_cache_included(self):
        from financial_data_query import _BATCH_CACHE_ATTRS
        assert '_excel_cache' in _BATCH_CACHE_ATTRS
        assert '_full_table_cache' in _BATCH_CACHE_ATTRS
        assert '_full_data_cache' in _BATCH_CACHE_ATTRS
        assert '_full_df_cache' in _BATCH_CACHE_ATTRS

    def test_ici_has_batch_cache(self):
        from financial_data_query import _has_batch_cache
        from financial_data_query.sources.ici import IciFetcher
        fetcher = IciFetcher()
        # IciFetcher has _excel_cache as a class attribute (dict), so it's always truthy
        # _has_batch_cache returns True if the attr is not None
        assert _has_batch_cache(fetcher, "ici") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
