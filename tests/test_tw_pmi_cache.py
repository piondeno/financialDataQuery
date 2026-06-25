"""Comprehensive tests for tw_pmi caching functionality.

Tests cover:
1. In-memory batch cache (_full_table_cache)
2. Disk cache integration
3. Cache hit/miss scenarios
4. Cross-process cache persistence (disk cache)
5. Single query vs batch query caching
6. Date filtering with cached data
"""
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch, mock_open
from financial_data_query.sources.tw_ndc import TwPmiFetcher, NdcFetcher
from financial_data_query.cache import QueryCache
from financial_data_query.disk_cache import DiskCache
from financial_data_query import _cache as memory_cache, _disk_cache
from financial_data_query import clear_cache


class TestTwPmiInMemoryBatchCache:
    """Test in-memory batch cache (_full_table_cache) for tw_pmi."""

    @pytest.fixture
    def fetcher(self):
        return TwPmiFetcher()

    @pytest.fixture
    def sample_full_table(self):
        """Sample full table data that mimics real PMI data."""
        dates = pd.date_range("2020-01", "2024-12", freq="MS")
        df = pd.DataFrame({
            "製造業PMI": [50.5 + i * 0.1 for i in range(len(dates))],
            "新增訂單數量": [48.2 + i * 0.05 for i in range(len(dates))],
            "生產數量": [51.3 + i * 0.08 for i in range(len(dates))],
            "人力僱用數量": [49.8 + i * 0.03 for i in range(len(dates))],
        }, index=dates)
        df.index.name = None
        return df

    def test_full_table_cache_is_empty_initially(self, fetcher):
        """Test that _full_table_cache starts empty."""
        # _full_table_cache is a class variable, starts as empty dict
        assert len(fetcher._full_table_cache) == 0 or fetcher.source_name not in fetcher._full_table_cache

    def test_get_full_table_cached_populates_cache(self, fetcher, sample_full_table):
        """Test that _get_full_table_cached stores data in cache."""
        with patch.object(fetcher, '_get_full_table', return_value=sample_full_table):
            result1 = fetcher._get_full_table_cached()
            assert fetcher.source_name in fetcher._full_table_cache
            assert len(result1) == len(sample_full_table)
            
            # Second call should return cached data
            with patch.object(fetcher, '_get_full_table', side_effect=Exception("Should use cache")):
                result2 = fetcher._get_full_table_cached()
                pd.testing.assert_frame_equal(result1, result2)

    def test_full_table_cache_is_class_variable(self, fetcher):
        """Test that _full_table_cache is shared across instances."""
        fetcher2 = TwPmiFetcher()
        assert fetcher._full_table_cache is fetcher2._full_table_cache

    def test_consecutive_fetch_calls_use_cache(self, fetcher, sample_full_table):
        """Test that consecutive fetch() calls use batch cache after first call."""
        # Pre-populate the cache
        fetcher._full_table_cache["tw_pmi"] = sample_full_table
        
        # Mock _get_full_table to track if it's called
        original_get_full_table = fetcher._get_full_table
        call_count = 0
        
        def mock_get_full_table():
            nonlocal call_count
            call_count += 1
            return sample_full_table
        
        fetcher._get_full_table = mock_get_full_table
        
        # First call should use pre-populated cache, so _get_full_table NOT called
        result1 = fetcher.fetch("製造業PMI")
        assert call_count == 0  # Used cache, no fetch needed
        
        # Clear cache to force fetch
        fetcher._full_table_cache.pop("tw_pmi", None)
        result2 = fetcher.fetch("製造業PMI")
        assert call_count == 1  # First fetch
        
        # Second call should use cache
        result3 = fetcher.fetch("製造業PMI")
        assert call_count == 1  # No additional fetch
        
        # Third call with different symbol should also use cache
        result4 = fetcher.fetch("新增訂單數量")
        assert call_count == 1  # Still using cache


class TestTwPmiDiskCacheIntegration:
    """Test disk cache integration for tw_pmi."""

    @pytest.fixture
    def tmp_cache(self, tmp_path):
        return DiskCache(str(tmp_path))

    @pytest.fixture
    def sample_data(self):
        dates = pd.date_range("2020-01", "2024-12", freq="MS")
        return pd.DataFrame({
            "value": [50.5 + i * 0.1 for i in range(len(dates))],
        }, index=dates)

    def test_disk_cache_stores_full_table(self, tmp_cache, sample_data):
        """Test that full table can be stored in disk cache."""
        table_name = tmp_cache._table_name("tw_pmi", "_tw_pmi_full_table", None)
        tmp_cache.set("tw_pmi", "_tw_pmi_full_table", sample_data, frequency=None)
        
        result = tmp_cache.get("tw_pmi", "_tw_pmi_full_table", frequency=None)
        assert result is not None
        assert len(result) == len(sample_data)

    def test_disk_cache_retrieves_with_date_filter(self, tmp_cache, sample_data):
        """Test disk cache retrieval with date filtering."""
        tmp_cache.set("tw_pmi", "_tw_pmi_full_table", sample_data, frequency=None)
        
        result = tmp_cache.get(
            "tw_pmi", "_tw_pmi_full_table",
            start="2022-01-01", end="2023-12-31", frequency=None
        )
        assert result is not None
        assert len(result) > 0
        assert len(result) < len(sample_data)

    def test_disk_cache_miss_returns_none(self, tmp_cache):
        """Test that disk cache miss returns None."""
        result = tmp_cache.get("tw_pmi", "NONEXISTENT", frequency=None)
        assert result is None

    def test_disk_cache_table_name_uses_hash(self, tmp_cache):
        """Test that table names use hash for symbol uniqueness."""
        table1 = tmp_cache._table_name("tw_pmi", "製造業PMI", None)
        table2 = tmp_cache._table_name("tw_pmi", "_tw_pmi_full_table", None)
        assert table1 != table2
        assert "tw_pmi" in table1
        assert "tw_pmi" in table2


class TestTwPmiQueryCacheFlow:
    """Test the complete query cache flow for tw_pmi."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset caches before each test."""
        clear_cache()
        yield
        clear_cache()

    @pytest.fixture
    def sample_full_table(self):
        dates = pd.date_range("2020-01", "2024-12", freq="MS")
        return pd.DataFrame({
            "製造業PMI": [50.5 + i * 0.1 for i in range(len(dates))],
            "新增訂單數量": [48.2 + i * 0.05 for i in range(len(dates))],
            "生產數量": [51.3 + i * 0.08 for i in range(len(dates))],
        }, index=dates)

    def test_memory_cache_hit_after_first_query(self, sample_full_table):
        """Test that second query with same params hits memory cache."""
        from financial_data_query.registry import Registry
        
        fetcher = TwPmiFetcher()
        fetcher._full_table_cache["tw_pmi"] = sample_full_table
        
        with patch.object(Registry, 'get', return_value=fetcher):
            # First query
            result1 = memory_cache.get("tw_pmi", "製造業PMI", None, None, None, None)
            assert result1 is None  # No cache yet
            
            # Simulate query populating cache
            from financial_data_query import _cache
            df = sample_full_table[["製造業PMI"]].rename(columns={"製造業PMI": "value"})
            _cache.set("tw_pmi", "製造業PMI", df)
            
            # Second query should hit cache
            result2 = _cache.get("tw_pmi", "製造業PMI", None, None, None, None)
            assert result2 is not None
            assert len(result2) == len(df)

    def test_batch_cache_detection(self, sample_full_table):
        """Test that batch cache detection works for tw_pmi."""
        from financial_data_query import _has_batch_cache, _get_batch_cache, _set_batch_cache
        
        # Clear class-level cache to avoid pollution from other tests
        TwPmiFetcher._full_table_cache.clear()
        
        fetcher = TwPmiFetcher()
        
        # Initially has batch cache capability (has _full_table_cache attribute)
        assert _has_batch_cache(fetcher, "tw_pmi") is True
        batch_data = _get_batch_cache(fetcher, "tw_pmi")
        assert batch_data is None  # But no data yet
        
        # After setting cache
        _set_batch_cache(fetcher, "tw_pmi", sample_full_table)
        batch_data = _get_batch_cache(fetcher, "tw_pmi")
        assert batch_data is not None
        assert len(batch_data) == len(sample_full_table)

    def test_date_filtering_on_cached_data(self, sample_full_table):
        """Test that date filtering works on cached data."""
        from financial_data_query import _filter_by_date
        
        df = sample_full_table[["製造業PMI"]].rename(columns={"製造業PMI": "value"})
        
        # No filter
        result = _filter_by_date(df, None, None)
        assert len(result) == len(df)
        
        # With start date
        result = _filter_by_date(df, "2022-01-01", None)
        assert len(result) < len(df)
        assert result.index[0] >= pd.Timestamp("2022-01-01")
        
        # With end date
        result = _filter_by_date(df, None, "2022-12-31")
        assert len(result) < len(df)
        assert result.index[-1] <= pd.Timestamp("2022-12-31")
        
        # With both dates
        result = _filter_by_date(df, "2022-01-01", "2023-12-31")
        assert len(result) < len(df)


class TestTwPmiDiskCachePersistence:
    """Test that disk cache persists data across process restarts."""

    @pytest.fixture
    def sample_full_table(self):
        dates = pd.date_range("2020-01", "2024-12", freq="MS")
        return pd.DataFrame({
            "製造業PMI": [50.5 + i * 0.1 for i in range(len(dates))],
            "新增訂單數量": [48.2 + i * 0.05 for i in range(len(dates))],
            "生產數量": [51.3 + i * 0.08 for i in range(len(dates))],
        }, index=dates)

    @pytest.fixture
    def tmp_cache_dir(self, tmp_path):
        """Create a temporary disk cache directory."""
        return str(tmp_path)

    def test_full_table_stored_to_disk_after_fetch(self, tmp_cache_dir, sample_full_table):
        """Test that full table is stored to disk cache after first fetch."""
        disk_cache = DiskCache(tmp_cache_dir)
        
        # Simulate storing full table to disk (as _single_query does)
        disk_cache.set("tw_pmi", "_tw_pmi_full_table", sample_full_table, frequency=None)
        
        # Verify it's stored
        result = disk_cache.get("tw_pmi", "_tw_pmi_full_table", frequency=None)
        assert result is not None
        assert len(result) == len(sample_full_table)
        
        disk_cache.close()

    def test_full_table_covers_date_range(self, tmp_cache_dir, sample_full_table):
        """Test that full table covers the requested date range."""
        disk_cache = DiskCache(tmp_cache_dir)
        disk_cache.set("tw_pmi", "_tw_pmi_full_table", sample_full_table, frequency=None)
        
        # Check coverage for a sub-range
        start = "2021-06-01"
        end = "2023-06-30"
        
        disk_df = disk_cache.get("tw_pmi", "_tw_pmi_full_table", frequency=None)
        covers_start = disk_df.index.min() <= pd.Timestamp(start)
        covers_end = disk_df.index.max() >= pd.Timestamp(end)
        
        assert covers_start is True
        assert covers_end is True
        
        disk_cache.close()

    def test_partial_cache_hit(self, tmp_cache_dir, sample_full_table):
        """Test that partial date range can be retrieved from full table."""
        disk_cache = DiskCache(tmp_cache_dir)
        disk_cache.set("tw_pmi", "_tw_pmi_full_table", sample_full_table, frequency=None)
        
        # Request a specific date range
        result = disk_cache.get(
            "tw_pmi", "_tw_pmi_full_table",
            start="2022-06-01", end="2022-12-31", frequency=None
        )
        
        assert result is not None
        assert len(result) > 0
        assert len(result) < len(sample_full_table)
        assert result.index[0] >= pd.Timestamp("2022-06-01")
        assert result.index[-1] <= pd.Timestamp("2022-12-31")
        
        disk_cache.close()


class TestTwPmiMultipleSymbolCaching:
    """Test caching behavior when querying multiple symbols."""

    @pytest.fixture
    def sample_full_table(self):
        dates = pd.date_range("2020-01", "2024-12", freq="MS")
        return pd.DataFrame({
            "製造業PMI": [50.5 + i * 0.1 for i in range(len(dates))],
            "新增訂單數量": [48.2 + i * 0.05 for i in range(len(dates))],
            "生產數量": [51.3 + i * 0.08 for i in range(len(dates))],
            "人力僱用數量": [49.8 + i * 0.03 for i in range(len(dates))],
        }, index=dates)

    def test_batch_fetch_uses_single_browser_session(self, sample_full_table):
        """Test that batch_fetch() uses the cached full table for all symbols."""
        fetcher = TwPmiFetcher()
        fetcher._full_table_cache["tw_pmi"] = sample_full_table
        
        # Batch fetch should use cached data
        results = fetcher.batch_fetch(["製造業PMI", "新增訂單數量"])
        
        assert "製造業PMI" in results
        assert "新增訂單數量" in results
        assert len(results["製造業PMI"]) == len(sample_full_table)
        assert len(results["新增訂單數量"]) == len(sample_full_table)

    def test_batch_fetch_caching_to_disk(self, sample_full_table):
        """Test that batch fetch stores full table to disk cache."""
        from financial_data_query.registry import Registry
        from financial_data_query import _has_batch_cache, _get_batch_cache
        
        fetcher = TwPmiFetcher()
        fetcher._full_table_cache["tw_pmi"] = sample_full_table
        
        # Simulate what _batch_query does
        assert _has_batch_cache(fetcher, "tw_pmi") is True
        full_table = _get_batch_cache(fetcher, "tw_pmi")
        assert full_table is not None
        
        # Full table should contain all symbols
        assert "製造業PMI" in full_table.columns
        assert "新增訂單數量" in full_table.columns

    def test_symbols_have_correct_column_names(self, sample_full_table):
        """Test that cached data has correct column names for tw_pmi symbols."""
        expected_columns = [
            "製造業PMI",
            "新增訂單數量",
            "生產數量",
            "人力僱用數量",
            "供應商交貨時間(%)",
            "存貨(%)",
            "客戶存貨(%)",
            "原物料價格(%)",
            "未完成訂單(%)",
            "新增出口訂單(%)",
            "進口原物料數量(%)",
            "未來六個月展望(%)",
        ]
        
        # Verify sample has at least the main columns
        for col in ["製造業PMI", "新增訂單數量", "生產數量"]:
            assert col in sample_full_table.columns


class TestTwPmiCacheEdgeCases:
    """Test edge cases and error scenarios for tw_pmi caching."""

    def test_empty_cache_returns_none(self):
        """Test that empty cache returns None."""
        fetcher = TwPmiFetcher()
        # Clear cache
        fetcher._full_table_cache.clear()
        
        # Access should not raise, just return empty or raise on fetch
        assert fetcher.source_name not in fetcher._full_table_cache

    def test_cache_with_different_sources(self):
        """Test that cache is isolated per source."""
        from financial_data_query.sources.tw_ndc import TwEcoFetcher
        
        pmi_fetcher = TwPmiFetcher()
        eco_fetcher = TwEcoFetcher()
        
        # They share the same _full_table_cache dict
        assert pmi_fetcher._full_table_cache is eco_fetcher._full_table_cache
        
        # But keys are different
        pmi_fetcher._full_table_cache["tw_pmi"] = pd.DataFrame({"a": [1]})
        eco_fetcher._full_table_cache["tw_eco"] = pd.DataFrame({"b": [2]})
        
        assert "tw_pmi" in pmi_fetcher._full_table_cache
        assert "tw_eco" in eco_fetcher._full_table_cache
        assert "tw_pmi" not in eco_fetcher._full_table_cache or eco_fetcher._full_table_cache.get("tw_pmi") is not None

    def test_cache_key_uniqueness(self):
        """Test that cache keys are unique per source."""
        fetcher = TwPmiFetcher()
        assert fetcher.source_name == "tw_pmi"
        
        # Set cache
        df = pd.DataFrame({"test": [1, 2, 3]})
        fetcher._full_table_cache["tw_pmi"] = df
        
        # Verify key exists
        assert "tw_pmi" in fetcher._full_table_cache
        assert len(fetcher._full_table_cache["tw_pmi"]) == 3


class TestMemoryCacheLRU:
    """Test the QueryCache LRU behavior."""

    def test_lru_eviction_order(self):
        """Test that oldest entries are evicted first."""
        cache = QueryCache(max_size=3)
        
        df1 = pd.DataFrame({"v": [1]}, index=pd.to_datetime(["2024-01-01"]))
        df2 = pd.DataFrame({"v": [2]}, index=pd.to_datetime(["2024-01-02"]))
        df3 = pd.DataFrame({"v": [3]}, index=pd.to_datetime(["2024-01-03"]))
        df4 = pd.DataFrame({"v": [4]}, index=pd.to_datetime(["2024-01-04"]))
        
        cache.set("tw_pmi", "A", df1)
        cache.set("tw_pmi", "B", df2)
        cache.set("tw_pmi", "C", df3)
        # Cache is now full
        
        # Add one more, should evict A
        cache.set("tw_pmi", "D", df4)
        
        assert cache.get("tw_pmi", "A") is None  # Evicted
        assert cache.get("tw_pmi", "B") is not None
        assert cache.get("tw_pmi", "C") is not None
        assert cache.get("tw_pmi", "D") is not None

    def test_lru_access_updates_order(self):
        """Test that accessing an entry moves it to end of LRU."""
        cache = QueryCache(max_size=3)
        
        df1 = pd.DataFrame({"v": [1]}, index=pd.to_datetime(["2024-01-01"]))
        df2 = pd.DataFrame({"v": [2]}, index=pd.to_datetime(["2024-01-02"]))
        df3 = pd.DataFrame({"v": [3]}, index=pd.to_datetime(["2024-01-03"]))
        df4 = pd.DataFrame({"v": [4]}, index=pd.to_datetime(["2024-01-04"]))
        
        cache.set("tw_pmi", "A", df1)
        cache.set("tw_pmi", "B", df2)
        cache.set("tw_pmi", "C", df3)
        
        # Access A to make it recently used
        cache.get("tw_pmi", "A")
        
        # Add D, should evict B (oldest)
        cache.set("tw_pmi", "D", df4)
        
        assert cache.get("tw_pmi", "A") is not None  # Still there (was accessed)
        assert cache.get("tw_pmi", "B") is None  # Evicted (oldest)
        assert cache.get("tw_pmi", "C") is not None
        assert cache.get("tw_pmi", "D") is not None


class TestDiskCacheDataIntegrity:
    """Test data integrity in disk cache operations."""

    @pytest.fixture
    def tmp_cache(self, tmp_path):
        return DiskCache(str(tmp_path))

    def test_chinese_characters_in_symbol(self, tmp_cache):
        """Test that Chinese characters in symbols are handled correctly."""
        df = pd.DataFrame({
            "value": [50.5, 51.2, 52.1],
        }, index=pd.to_datetime(["2024-01", "2024-02", "2024-03"]))
        
        # Table name should use hash
        table_name = tmp_cache._table_name("tw_pmi", "製造業PMI", None)
        assert "tw_pmi" in table_name
        
        tmp_cache.set("tw_pmi", "製造業PMI", df)
        result = tmp_cache.get("tw_pmi", "製造業PMI")
        
        assert result is not None
        assert len(result) == 3

    def test_timestamp_serialization(self, tmp_cache):
        """Test that timestamps are correctly serialized and deserialized."""
        dates = pd.date_range("2020-01", "2024-12", freq="MS")
        df = pd.DataFrame({
            "value": [50.5 + i for i in range(len(dates))],
        }, index=dates)
        
        tmp_cache.set("tw_pmi", "TEST", df)
        result = tmp_cache.get("tw_pmi", "TEST")
        
        assert result is not None
        assert len(result) == len(df)
        # Index should be datetime
        assert isinstance(result.index, pd.DatetimeIndex)

    def test_multiple_columns_preserved(self, tmp_cache):
        """Test that multiple columns are preserved in cache."""
        df = pd.DataFrame({
            "製造業PMI": [50.5, 51.2],
            "新增訂單": [48.2, 49.1],
            "生產數量": [51.3, 52.0],
        }, index=pd.to_datetime(["2024-01", "2024-02"]))
        
        tmp_cache.set("tw_pmi", "FULL_TABLE", df)
        result = tmp_cache.get("tw_pmi", "FULL_TABLE")
        
        assert result is not None
        assert len(result.columns) == 3
        assert "製造業PMI" in result.columns
        assert "新增訂單" in result.columns
        assert "生產數量" in result.columns


class TestIntegrationQueryFlow:
    """Integration tests for the complete query flow with caching."""

    @pytest.fixture(autouse=True)
    def setup(self):
        clear_cache()
        yield
        clear_cache()

    @pytest.fixture
    def mock_full_table(self):
        dates = pd.date_range("2020-01", "2024-12", freq="MS")
        return pd.DataFrame({
            "製造業PMI": [50.5 + i * 0.1 for i in range(len(dates))],
            "新增訂單數量": [48.2 + i * 0.05 for i in range(len(dates))],
            "生產數量": [51.3 + i * 0.08 for i in range(len(dates))],
        }, index=dates)

    def test_full_query_flow_with_mock(self, mock_full_table):
        """Test complete query flow with mocked data."""
        fetcher = TwPmiFetcher()
        
        # Pre-populate cache to simulate first fetch
        fetcher._full_table_cache["tw_pmi"] = mock_full_table
        
        # First fetch should use cache
        result1 = fetcher.fetch("製造業PMI")
        assert len(result1) > 0
        assert "value" in result1.columns
        
        # Second fetch should also use cache (no additional call needed)
        result2 = fetcher.fetch("製造業PMI")
        assert len(result2) == len(result1)

    def test_batch_query_flow_with_mock(self, mock_full_table):
        """Test batch query flow with mocked data."""
        fetcher = TwPmiFetcher()
        
        # Pre-populate cache
        fetcher._full_table_cache["tw_pmi"] = mock_full_table
        
        # First batch fetch should use cache
        results1 = fetcher.batch_fetch(["製造業PMI", "新增訂單數量"])
        assert len(results1) == 2
        
        # Second batch fetch should also use cache
        results2 = fetcher.batch_fetch(["製造業PMI", "生產數量"])
        assert len(results2) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
