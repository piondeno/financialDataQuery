import pandas as pd
from financial_data_query.base import _check_cache_gaps


class TestCheckCacheGaps:
    """Tests for _check_cache_gaps — detects disjoint date ranges in cached data."""

    # --- Basic cases ---

    def test_empty_df_returns_true(self):
        df = pd.DataFrame({"v": []}, index=pd.DatetimeIndex([], dtype="datetime64[ns]"))
        assert _check_cache_gaps(df, "2020-01-01", "2022-12-31", None) is True

    def test_too_few_rows_returns_false(self):
        df = pd.DataFrame({"v": [1, 2]}, index=pd.date_range("2020-01-01", periods=2))
        assert _check_cache_gaps(df, "2020-01-01", "2020-01-02", None) is False

    def test_continuous_daily_data_no_gap(self):
        df = pd.DataFrame({"v": [1]}, index=pd.date_range("2020-01-01", periods=365, freq="D"))
        assert _check_cache_gaps(df, "2020-01-01", "2020-12-31", None) is False

    def test_continuous_daily_data_no_gap_with_freq(self):
        df = pd.DataFrame({"v": [1]}, index=pd.date_range("2020-01-01", periods=365, freq="D"))
        assert _check_cache_gaps(df, "2020-01-01", "2020-12-31", "daily") is False

    # --- Gap detection ---

    def test_large_gap_detected_daily(self):
        """A gap of 10 days in daily data should be detected."""
        idx = (
            pd.date_range("2020-01-01", periods=10, freq="D")
            .append(pd.date_range("2020-01-20", periods=10, freq="D"))
        )
        df = pd.DataFrame({"v": range(len(idx))}, index=idx)
        assert _check_cache_gaps(df, "2020-01-01", "2020-01-30", None) is True

    def test_one_day_gap_no_detection(self):
        """A 1-day gap in daily data (weekend) should not be detected."""
        idx = (
            pd.date_range("2020-01-01", periods=30, freq="D")
            .append(pd.date_range("2020-02-01", periods=10, freq="D"))
        )
        df = pd.DataFrame({"v": range(len(idx))}, index=idx)
        assert _check_cache_gaps(df, "2020-01-01", "2020-02-10", None) is False

    # --- The core scenario: disjoint year ranges ---

    def test_disjoint_year_2020_and_2022_no_2021(self):
        """The exact scenario: 2020 + 2022 data, queried for 2021-06 ~ 2022-06."""
        idx = (
            pd.date_range("2020-01-01", periods=20, freq="D")
            .append(pd.date_range("2022-01-01", periods=20, freq="D"))
        )
        df = pd.DataFrame({"v": range(len(idx))}, index=idx)
        # Query range that spans the gap
        assert _check_cache_gaps(df, "2021-06-01", "2022-06-01", None) is True

    # --- Weekly frequency ---

    def test_continuous_weekly_no_gap(self):
        df = pd.DataFrame({"v": [1]}, index=pd.date_range("2020-01-01", periods=100, freq="W"))
        assert _check_cache_gaps(df, "2020-01-01", "2021-01-01", "weekly") is False

    def test_large_gap_weekly_detected(self):
        """A 3-month gap in weekly data should be detected (threshold is 21 days)."""
        idx = (
            pd.date_range("2020-01-01", periods=20, freq="W")
            .append(pd.date_range("2020-08-01", periods=20, freq="W"))
        )
        df = pd.DataFrame({"v": range(len(idx))}, index=idx)
        assert _check_cache_gaps(df, "2020-01-01", "2020-12-01", "weekly") is True

    # --- Monthly frequency ---

    def test_continuous_monthly_no_gap(self):
        df = pd.DataFrame({"v": [1]}, index=pd.date_range("2020-01-01", periods=36, freq="MS"))
        assert _check_cache_gaps(df, "2020-01-01", "2022-12-01", "monthly") is False

    def test_large_gap_monthly_detected(self):
        """A 6-month gap in monthly data should be detected (threshold is 60 days)."""
        idx = (
            pd.date_range("2020-01-01", periods=12, freq="MS")
            .append(pd.date_range("2021-09-01", periods=12, freq="MS"))
        )
        df = pd.DataFrame({"v": range(len(idx))}, index=idx)
        assert _check_cache_gaps(df, "2020-01-01", "2022-08-01", "monthly") is True

    # --- Edge cases ---

    def test_unknown_frequency_returns_false(self):
        df = pd.DataFrame({"v": [1]}, index=pd.date_range("2020-01-01", periods=10, freq="D"))
        assert _check_cache_gaps(df, "2020-01-01", "2020-01-10", "hourly") is False

    def test_non_datetime_index_coerced(self):
        """Non-DatetimeIndex should still work (diffs will be in days)."""
        idx = pd.Index(["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-20"])
        df = pd.DataFrame({"v": [1, 2, 3, 4]}, index=idx)
        assert _check_cache_gaps(df, "2020-01-01", "2020-01-30", None) is True

    def test_single_gap_in_middle(self):
        """One large gap in an otherwise continuous series."""
        idx = (
            pd.date_range("2020-01-01", periods=50, freq="D")
            .append(pd.date_range("2020-04-01", periods=50, freq="D"))
        )
        df = pd.DataFrame({"v": range(len(idx))}, index=idx)
        assert _check_cache_gaps(df, "2020-01-01", "2020-05-30", None) is True

    def test_tz_aware_index(self):
        """Timezone-aware index should be handled correctly."""
        idx = pd.date_range("2020-01-01", periods=10, freq="D", tz="UTC")
        df = pd.DataFrame({"v": range(10)}, index=idx)
        assert _check_cache_gaps(df, "2020-01-01", "2020-01-10", None) is False

    # --- Edge: query range outside all cached data ---

    def test_gap_only_at_query_boundary(self):
        """Gap at the very boundary of the query range should still be detected."""
        # Continuous data up to 2020-06-01, then a gap, then 2020-09-01 onwards
        idx = (
            pd.date_range("2020-01-01", periods=100, freq="D")
            .append(pd.date_range("2020-09-01", periods=100, freq="D"))
        )
        df = pd.DataFrame({"v": range(len(idx))}, index=idx)
        assert _check_cache_gaps(df, "2020-01-01", "2020-12-01", None) is True
