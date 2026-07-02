"""Integration tests for cache gap detection — verifies end-to-end behavior with disjoint date ranges."""
import os
import sys
import tempfile
import pandas as pd

from financial_data_query.disk_cache import DiskCache
from financial_data_query.base import DataSourceFetcher, _filter_by_date, _check_cache_gaps


class MockFetcher(DataSourceFetcher):
    """Mock fetcher that returns continuous data on fetch (simulates API call)."""

    source_name = "mock"

    def fetch(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
        frequency: str | None = None,
    ) -> pd.DataFrame:
        # Simulate fetching full range from API
        if not start:
            start = "2020-01-01"
        if not end:
            end = "2022-12-31"
        idx = pd.date_range(start, end, freq="D")
        df = pd.DataFrame({"value": range(len(idx))}, index=idx)
        return df


class TestGapDetectionIntegration:
    """Test that the gap detection mechanism works end-to-end through the query pipeline."""

    def setup_method(self):
        """Create a temporary disk cache for each test."""
        self.tmpdir = tempfile.mkdtemp()
        self.disk_cache = DiskCache(cache_dir=self.tmpdir)

    def teardown_method(self):
        self.disk_cache.close()
        try:
            import shutil
            shutil.rmtree(self.tmpdir)
        except OSError:
            pass

    def test_disjoint_cache_triggers_gap_detection(self):
        """Core scenario: 2020 + 2022 in cache, query for 2021-06 ~ 2022-06 should detect gap."""
        # Simulate: 2020 data was fetched and cached first
        idx_2020 = pd.date_range("2020-01-01", "2020-12-31", freq="D")
        df_2020 = pd.DataFrame({"value": range(len(idx_2020))}, index=idx_2020)
        self.disk_cache.set("mock", "AAPL", df_2020, frequency=None)

        # Then 2022 data was fetched and cached (merged with 2020)
        idx_2022 = pd.date_range("2022-01-01", "2022-12-31", freq="D")
        df_2022 = pd.DataFrame({"value": range(len(idx_2022))}, index=idx_2022)
        existing = self.disk_cache.get("mock", "AAPL", frequency=None)
        merged = pd.concat([existing, df_2022])
        merged = merged[~merged.index.duplicated(keep="first")]
        merged.sort_index(inplace=True)
        self.disk_cache.set("mock", "AAPL", merged, frequency=None)

        # Now query for 2021-06 ~ 2022-06
        # Get full cached data (simulating what _single_query Step 3 does)
        disk_df = self.disk_cache.get("mock", "AAPL", frequency=None)

        # Verify covers_start and covers_end would both be True
        assert disk_df.index.min() <= pd.Timestamp("2021-06-01")  # covers_start
        assert disk_df.index.max() >= pd.Timestamp("2022-06-01")  # covers_end

        # Gap detection on full data should detect the 2021 gap
        assert _check_cache_gaps(disk_df, "2021-06-01", "2022-06-01", None) is True

        # Without gap detection, the filter would return only 2022 data (partial)
        filtered = _filter_by_date(disk_df, "2021-06-01", "2022-06-01")
        assert len(filtered) > 0  # Has 2022 data
        assert len(filtered) < 366  # Missing 2021 data

    def test_continuous_cache_no_gap(self):
        """Continuous data in cache — gap detection should NOT trigger."""
        idx = pd.date_range("2020-01-01", "2022-12-31", freq="D")
        df = pd.DataFrame({"value": range(len(idx))}, index=idx)
        self.disk_cache.set("mock", "AAPL", df, frequency=None)

        disk_df = self.disk_cache.get("mock", "AAPL", frequency=None)
        assert _check_cache_gaps(disk_df, "2021-06-01", "2022-06-01", None) is False

        # Filter returns full range
        filtered = _filter_by_date(disk_df, "2021-06-01", "2022-06-01")
        assert len(filtered) > 365  # Has full 2021-2022 data

    def test_small_gap_weekend_no_detection(self):
        """Weekend gaps (2-3 days) in daily data should NOT be detected."""
        # Create data with only weekend gaps (Mon-Fri)
        dates = pd.bdate_range("2020-01-01", "2020-06-30", freq="B")
        df = pd.DataFrame({"value": range(len(dates))}, index=dates)
        self.disk_cache.set("mock", "AAPL", df, frequency=None)

        disk_df = self.disk_cache.get("mock", "AAPL", frequency=None)
        assert _check_cache_gaps(disk_df, "2020-01-01", "2020-06-30", None) is False

    def test_weekly_data_continuous(self):
        """Continuous weekly data should not trigger gap detection."""
        idx = pd.date_range("2020-01-01", "2022-12-31", freq="W")
        df = pd.DataFrame({"value": range(len(idx))}, index=idx)
        self.disk_cache.set("mock", "AAPL", df, frequency="weekly")

        disk_df = self.disk_cache.get("mock", "AAPL", frequency="weekly")
        assert _check_cache_gaps(disk_df, "2020-01-01", "2022-12-31", "weekly") is False

    def test_weekly_data_with_gap(self):
        """Weekly data with a 3-month gap should be detected."""
        idx = (
            pd.date_range("2020-01-01", periods=20, freq="W")
            .append(pd.date_range("2020-08-01", periods=20, freq="W"))
        )
        df = pd.DataFrame({"value": range(len(idx))}, index=idx)
        self.disk_cache.set("mock", "AAPL", df, frequency="weekly")

        disk_df = self.disk_cache.get("mock", "AAPL", frequency="weekly")
        assert _check_cache_gaps(disk_df, "2020-01-01", "2020-12-31", "weekly") is True

    def test_monthly_data_with_gap(self):
        """Monthly data with a 6-month gap should be detected."""
        idx = (
            pd.date_range("2020-01-01", periods=12, freq="MS")
            .append(pd.date_range("2021-09-01", periods=12, freq="MS"))
        )
        df = pd.DataFrame({"value": range(len(idx))}, index=idx)
        self.disk_cache.set("mock", "AAPL", df, frequency="monthly")

        disk_df = self.disk_cache.get("mock", "AAPL", frequency="monthly")
        assert _check_cache_gaps(disk_df, "2020-01-01", "2022-08-01", "monthly") is True

    def test_three_way_disjoint(self):
        """Three separate ranges: 2020 + 2021-06 + 2022. Querying full range should detect gaps."""
        idx = (
            pd.date_range("2020-01-01", periods=20, freq="D")
            .append(pd.date_range("2021-06-01", periods=20, freq="D"))
            .append(pd.date_range("2022-01-01", periods=20, freq="D"))
        )
        df = pd.DataFrame({"value": range(len(idx))}, index=idx)
        self.disk_cache.set("mock", "AAPL", df, frequency=None)

        disk_df = self.disk_cache.get("mock", "AAPL", frequency=None)
        assert _check_cache_gaps(disk_df, "2020-01-01", "2022-01-30", None) is True

    def test_cache_merge_simulation(self):
        """Simulate the actual cache merge flow that creates disjoint data."""
        fetcher = MockFetcher()

        # Query 1: 2020 only
        df1 = fetcher.fetch("AAPL", start="2020-01-01", end="2020-12-31")
        df1_filtered = _filter_by_date(df1, "2020-01-01", "2020-12-31")
        self.disk_cache.set("mock", "AAPL", df1_filtered, frequency=None)

        # Query 2: 2022 only (simulates merging with existing cache)
        df2 = fetcher.fetch("AAPL", start="2022-01-01", end="2022-12-31")
        df2_filtered = _filter_by_date(df2, "2022-01-01", "2022-12-31")
        existing = self.disk_cache.get("mock", "AAPL", frequency=None)
        merged = pd.concat([existing, df2_filtered])
        merged = merged[~merged.index.duplicated(keep="first")]
        merged.sort_index(inplace=True)
        self.disk_cache.set("mock", "AAPL", merged, frequency=None)

        # Query 3: 2021-06 ~ 2022-06 — the problematic scenario
        disk_df = self.disk_cache.get("mock", "AAPL", frequency=None)

        # This is what the old code would check:
        covers_start = disk_df.index.min() <= pd.Timestamp("2021-06-01")
        covers_end = disk_df.index.max() >= pd.Timestamp("2022-06-01")
        assert covers_start and covers_end  # Both True — cache hit

        # Without gap detection, filter returns only 2022 data
        filtered = _filter_by_date(disk_df, "2021-06-01", "2022-06-01")
        assert len(filtered) > 0 and len(filtered) < 366  # Partial data

        # With gap detection, the gap is found on full data
        assert _check_cache_gaps(disk_df, "2021-06-01", "2022-06-01", None) is True
        # This triggers a re-fetch from the API
