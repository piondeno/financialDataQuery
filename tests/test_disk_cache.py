import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
from financial_data_query.disk_cache import DiskCache


class TestAutoFrequency:
    """Test auto frequency selection logic."""

    @pytest.fixture(autouse=True)
    def _reload_module(self):
        # Re-import to get fresh module state
        from financial_data_query import _auto_frequency
        self._auto_frequency = _auto_frequency

    def test_daily_for_short_range(self):
        assert self._auto_frequency("yahoo", "2024-01-01", "2024-12-31", None) == "daily"

    def test_weekly_for_medium_range(self):
        freq = self._auto_frequency("yahoo", "2020-01-01", "2023-12-31", None)
        assert freq == "weekly"

    def test_monthly_for_long_range(self):
        freq = self._auto_frequency("yahoo", "2015-01-01", "2026-01-01", None)
        assert freq == "monthly"

    def test_daily_when_no_dates(self):
        assert self._auto_frequency("yahoo", None, None, None) == "daily"

    def test_none_for_non_frequency_aware_source(self):
        assert self._auto_frequency("fred", "2024-01-01", "2024-12-31", None) is None

    def test_user_specified_takes_precedence(self):
        assert (
            self._auto_frequency("yahoo", "2024-01-01", "2024-12-31", "weekly")
            == "weekly"
        )


class TestDiskCache:
    """Test disk cache operations."""

    @pytest.fixture
    def tmp_cache(self, tmp_path):
        return DiskCache(str(tmp_path))

    def test_table_name_sanitization(self, tmp_cache):
        assert (
            tmp_cache._table_name("yahoo", "^GSPC", "daily") == "yahoo__GSPC_daily"
        )
        assert tmp_cache._table_name("fred", "GDP", None) == "fred_GDP_none"

    def test_set_and_get(self, tmp_cache):
        df = pd.DataFrame(
            {"Open": [100, 101], "Close": [102, 103]},
            index=pd.to_datetime(["2024-01-01", "2024-01-02"]),
        )
        tmp_cache.set("yahoo", "TEST", df, frequency="daily")

        result = tmp_cache.get(
            "yahoo", "TEST", start="2024-01-01", end="2024-01-02", frequency="daily"
        )
        assert result is not None
        assert len(result) == 2

    def test_get_with_date_filter(self, tmp_cache):
        df = pd.DataFrame(
            {"Open": [100, 101, 102], "Close": [103, 104, 105]},
            index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
        )
        tmp_cache.set("yahoo", "TEST", df, frequency="daily")

        result = tmp_cache.get(
            "yahoo", "TEST", start="2024-01-02", end="2024-01-03", frequency="daily"
        )
        assert len(result) == 2

    def test_get_miss_returns_none(self, tmp_cache):
        result = tmp_cache.get(
            "yahoo", "NONEXISTENT", start=None, end=None, frequency="daily"
        )
        assert result is None

    def test_merge_data_on_update(self, tmp_cache):
        df1 = pd.DataFrame(
            {"Open": [100], "Close": [102]},
            index=pd.to_datetime(["2024-01-01"]),
        )
        tmp_cache.set("yahoo", "TEST", df1, frequency="daily")

        df2 = pd.DataFrame(
            {"Open": [103], "Close": [105]},
            index=pd.to_datetime(["2024-01-02"]),
        )
        existing = tmp_cache.get("yahoo", "TEST", frequency="daily")
        merged = pd.concat([existing, df2])
        merged = merged[~merged.index.duplicated(keep="first")]
        merged.sort_index(inplace=True)
        tmp_cache.set("yahoo", "TEST", merged, frequency="daily")

        result = tmp_cache.get("yahoo", "TEST", frequency="daily")
        assert len(result) == 2


class TestDiskCacheCleanup:
    """Test old file cleanup behavior."""

    def test_old_files_removed_on_init(self, tmp_path):
        # Create an old database file
        (tmp_path / "2024-01-01.db").touch()
        assert list(tmp_path.glob("*.db"))

        # Initialize DiskCache which should clean up old files
        dc = DiskCache(str(tmp_path))
        db_files = list(tmp_path.glob("*.db"))
        assert len(db_files) == 1
        assert "2024-01-01" not in db_files[0].name


class TestQueryIntegration:
    """Test query integration with disk cache."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self._patches = []
        yield
        for p in self._patches:
            p.stop()

    def _mock_fetcher(self, df):
        fetcher = MagicMock()
        fetcher.source_name = "test_source"
        fetcher.fetch.return_value = df
        fetcher.batch_fetch.return_value = {"TEST": df}
        return fetcher

    @pytest.fixture
    def tmp_cache_dir(self, tmp_path):
        # Patch the disk cache to use a temp directory
        from financial_data_query import _disk_cache
        old_cache = _disk_cache
        new_cache = DiskCache(str(tmp_path))
        import financial_data_query as fdq

        fdq._disk_cache = new_cache
        yield tmp_path, new_cache
        fdq._disk_cache = old_cache
        new_cache.close()

    def test_first_query_populates_disk_cache(self, tmp_cache_dir):
        from financial_data_query import _disk_cache, clear_cache

        df = pd.DataFrame(
            {"Open": [100], "Close": [102]},
            index=pd.to_datetime(["2024-01-01"]),
        )

        with patch("financial_data_query.Registry.get") as mock_get:
            fetcher = self._mock_fetcher(df)
            mock_get.return_value = fetcher

            import financial_data_query as fdq
            clear_cache()  # Clear in-memory cache for this test

            result = fdq.query(
                "test_source",
                "TEST",
                start="2024-01-01",
                end="2024-01-01",
                output="dataframe",
            )

        assert len(result) == 1
        disk_result = _disk_cache.get("test_source", "TEST", frequency="none")
        assert disk_result is not None
        assert len(disk_result) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
