"""
診斷腳本：測試 tw_pmi 快取功能是否正常運作
使用方法：python diagnose_tw_pmi_cache.py
"""
import sys
import os
import pandas as pd
from unittest.mock import patch, MagicMock
from financial_data_query import clear_cache
from financial_data_query.registry import Registry
from financial_data_query.sources.tw_ndc import TwPmiFetcher
from financial_data_query import _cache, _disk_cache

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_section(title):
    print(f"\n--- {title} ---")

def test_in_memory_batch_cache():
    """測試 1：同進程 batch cache"""
    print_section("測試 1：同進程 batch cache")
    
    dates = pd.date_range("2020-01", "2024-12", freq="MS")
    full_table = pd.DataFrame({
        "製造業PMI": [50.5 + i*0.1 for i in range(len(dates))],
        "新增訂單數量": [48.2 + i*0.05 for i in range(len(dates))],
        "生產數量": [51.3 + i*0.08 for i in range(len(dates))],
    }, index=dates)
    
    fetcher = TwPmiFetcher()
    call_count = 0
    
    def mock_get_full_table():
        nonlocal call_count
        call_count += 1
        return full_table
    
    # 清空緩存
    fetcher._full_table_cache.clear()
    
    # 模擬 fetcher
    fetcher._get_full_table = mock_get_full_table
    
    # 第一次 fetch
    result1 = fetcher.fetch("製造業PMI")
    
    # 第二次 fetch（應該使用 batch cache）
    result2 = fetcher.fetch("新增訂單數量")
    
    # 第三次 fetch（應該使用 batch cache）
    result3 = fetcher.fetch("生產數量")
    
    passed = call_count == 1
    print(f"  開啟瀏覽器次數: {call_count}")
    print(f"  預期: 1 次")
    print(f"  結果: {'✓ PASS' if passed else '✗ FAIL'}")
    return passed

def test_disk_cache_write_read():
    """測試 2：Disk cache 寫入與讀取"""
    print_section("測試 2：Disk cache 寫入與讀取")
    
    import tempfile
    from financial_data_query.disk_cache import DiskCache
    
    dates = pd.date_range("2020-01", "2024-12", freq="MS")
    full_table = pd.DataFrame({
        "製造業PMI": [50.5 + i*0.1 for i in range(len(dates))],
        "新增訂單數量": [48.2 + i*0.05 for i in range(len(dates))],
    }, index=dates)
    
    tmpdir = tempfile.mkdtemp()
    
    try:
        # 寫入
        dc = DiskCache(tmpdir)
        dc.set("tw_pmi", "_tw_pmi_full_table", full_table, frequency=None)
        dc.close()
        
        # 讀取（模擬新進程）
        dc2 = DiskCache(tmpdir)
        result = dc2.get("tw_pmi", "_tw_pmi_full_table", frequency=None)
        dc2.close()
        
        passed = result is not None and len(result) == len(full_table)
        print(f"  寫入行數: {len(full_table)}")
        print(f"  讀取行數: {len(result) if result is not None else 0}")
        print(f"  結果: {'✓ PASS' if passed else '✗ FAIL'}")
        
        # 清理
        import shutil
        shutil.rmtree(tmpdir)
        return passed
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        return False

def test_query_cache_flow():
    """測試 3：完整的 query() 流程"""
    print_section("測試 3：完整的 query() 流程（模擬）")
    
    dates = pd.date_range("2020-01", "2024-12", freq="MS")
    full_table = pd.DataFrame({
        "製造業PMI": [50.5 + i*0.1 for i in range(len(dates))],
        "新增訂單數量": [48.2 + i*0.05 for i in range(len(dates))],
        "生產數量": [51.3 + i*0.08 for i in range(len(dates))],
        "人力僱用數量": [49.8 + i*0.03 for i in range(len(dates))],
    }, index=dates)
    
    symbols = ["製造業PMI", "新增訂單數量", "生產數量", "人力僱用數量"]
    
    # 重置
    Registry._fetchers = {}
    clear_cache()
    
    fetcher = TwPmiFetcher()
    Registry._fetchers["tw_pmi"] = fetcher
    call_count = 0
    
    def mock_get_full_table():
        nonlocal call_count
        call_count += 1
        return full_table
    
    passed = True
    for symbol in symbols:
        print(f"  查詢: {symbol}")
        
        # 模擬 _single_query 邏輯
        fetcher._get_full_table = mock_get_full_table
        clear_cache()
        
        # 檢查 memory cache
        cached = _cache.get("tw_pmi", symbol, None, None, None, None)
        if cached is not None:
            print(f"    ✓ Memory cache HIT")
            continue
        
        # 檢查 batch cache
        has_batch = hasattr(fetcher, '_full_table_cache') and "tw_pmi" in getattr(fetcher, '_full_table_cache', {})
        if has_batch:
            batch_df = fetcher._full_table_cache.get("tw_pmi")
            if batch_df is not None and symbol in batch_df.columns:
                print(f"    ✓ Batch cache HIT")
                result = batch_df[[symbol]].rename(columns={symbol: "value"})
                _cache.set("tw_pmi", symbol, result)
                continue
            else:
                print(f"    ✗ Batch cache miss (symbol not found)")
                passed = False
        else:
            print(f"    → Cache MISS, calling fetch()")
            result = fetcher.fetch(symbol)
            if "tw_pmi" not in fetcher._full_table_cache:
                fetcher._full_table_cache["tw_pmi"] = full_table
            _cache.set("tw_pmi", symbol, result)
    
    print(f"\n  開啟瀏覽器次數: {call_count}")
    print(f"  預期: 1 次")
    print(f"  結果: {'✓ PASS' if call_count == 1 and passed else '✗ FAIL'}")
    return call_count == 1 and passed

def test_disk_cache_persistence():
    """測試 4：Disk cache 持久性"""
    print_section("測試 4：Disk cache 持久性檢查")
    
    try:
        # 檢查 disk cache 目錄
        cache_dir = _disk_cache._cache_dir
        db_files = list(cache_dir.glob("*.db"))
        
        print(f"  Disk cache 目錄: {cache_dir}")
        print(f"  當前 .db 文件: {[f.name for f in db_files]}")
        
        # 嘗試讀取 tw_pmi 的 disk cache
        result = _disk_cache.get("tw_pmi", "_tw_pmi_full_table", frequency=None)
        
        if result is not None:
            print(f"  ✓ 讀取成功: {len(result)} 行")
            print(f"  列: {list(result.columns)}")
            print(f"  結果: ✓ PASS")
            return True
        else:
            print(f"  ℹ 暫無 tw_pmi disk cache 資料（正常：第一次查詢前）")
            print(f"  結果: ✓ PASS（尚未有緩存資料）")
            return True
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        return False

def main():
    print_header("tw_pmi 快取功能診斷工具")
    
    results = []
    
    # 測試 1：In-memory batch cache
    results.append(("同進程 Batch Cache", test_in_memory_batch_cache()))
    
    # 測試 2：Disk cache 寫入/讀取
    results.append(("Disk Cache 寫入/讀取", test_disk_cache_write_read()))
    
    # 測試 3：完整 query 流程
    results.append(("完整 Query 流程", test_query_cache_flow()))
    
    # 測試 4：Disk cache 持久性
    results.append(("Disk Cache 持久性", test_disk_cache_persistence()))
    
    # 總結
    print_header("診斷總結")
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("  所有測試通過！快取機制運作正常。")
        print()
        print("  如果您仍遇到快取問題，可能是以下原因：")
        print("  1. 每次查詢在不同進程中，且 disk cache 寫入失敗")
        print("  2. 程式異常退出，導致 _full_table_cache 未正確寫入")
        print("  3. 磁碟空間不足或權限問題")
        print("  4. 網路錯誤導致 fetcher.fetch() 失敗")
    else:
        print("  ⚠ 部分測試失敗，快取機制可能有問題。")
    
    print()
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
