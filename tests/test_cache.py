import pandas as pd
from financial_data_query.cache import QueryCache


def test_cache_get_miss():
    cache = QueryCache()
    result = cache.get("yahoo", "AAPL")
    assert result is None


def test_cache_set_and_get():
    cache = QueryCache()
    df = pd.DataFrame({"close": [100]}, index=pd.to_datetime(["2024-01-01"]))
    cache.set("yahoo", "AAPL", df)
    result = cache.get("yahoo", "AAPL")
    pd.testing.assert_frame_equal(result, df)


def test_cache_clear():
    cache = QueryCache()
    df = pd.DataFrame({"close": [100]}, index=pd.to_datetime(["2024-01-01"]))
    cache.set("yahoo", "AAPL", df)
    cache.clear()
    assert cache.get("yahoo", "AAPL") is None


def test_cache_max_size_evicts_oldest():
    cache = QueryCache(max_size=3)
    df = pd.DataFrame({"v": [1]}, index=pd.to_datetime(["2024-01-01"]))
    cache.set("s", "a", df.copy())
    cache.set("s", "b", df.copy())
    cache.set("s", "c", df.copy())
    cache.set("s", "d", df.copy())
    assert cache.get("s", "a") is None
    assert cache.get("s", "d") is not None


def test_cache_with_sub_field():
    cache = QueryCache()
    df1 = pd.DataFrame({"close": [1]}, index=pd.to_datetime(["2024-01-01"]))
    df2 = pd.DataFrame({"open": [2]}, index=pd.to_datetime(["2024-01-01"]))
    cache.set("yahoo", "AAPL", df1, sub_field="close")
    cache.set("yahoo", "AAPL", df2, sub_field="open")
    result_close = cache.get("yahoo", "AAPL", sub_field="close")
    result_open = cache.get("yahoo", "AAPL", sub_field="open")
    pd.testing.assert_frame_equal(result_close, df1)
    pd.testing.assert_frame_equal(result_open, df2)
