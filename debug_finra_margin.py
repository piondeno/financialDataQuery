#!/usr/bin/env python
"""FinraMargin 除錯測試腳本"""
import os
import sys
import time
import urllib.request
import pandas as pd

FINRA_URL = "https://www.finra.org/sites/default/files/2021-03/margin-statistics.xlsx"
SHEET_NAME = "Customer Margin Balances"
TMP_DIR = "/tmp"

_SYMBOL_MAP = {
    "debit_balances": "Debit Balances in Customers' Securities Margin Accounts",
    "free_credit_cash": "Free Credit Balances in Customers' Cash Accounts",
    "free_credit_margin": "Free Credit Balances in Customers' Securities Margin Accounts",
}


def main():
    # Step 1: 下載 Excel
    print("[Step 1] 下載 Excel 檔案...")
    timestamp = int(time.time())
    tmp_path = os.path.join(TMP_DIR, f"margin-statistics-{timestamp}.xlsx")
    try:
        start_t = time.time()
        urllib.request.urlretrieve(FINRA_URL, tmp_path)
        elapsed = time.time() - start_t
        file_size = os.path.getsize(tmp_path)
        print(f"  下載完成: {tmp_path}")
        print(f"  檔案大小: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        print(f"  耗時: {elapsed:.2f}s")
    except Exception as e:
        print(f"  下載失敗: {e}")
        return
    input(">>> 按 Enter 繼續...\n")

    # Step 2: 讀取 Excel
    print("[Step 2] 讀取 Excel 檔案...")
    try:
        df = pd.read_excel(tmp_path, sheet_name=SHEET_NAME, engine="openpyxl")
        print(f"  Sheet: {SHEET_NAME}")
        print(f"  Shape: {df.shape}")
        print(f"  Columns: {list(df.columns)}")
        print(f"  Dtypes:\n{df.dtypes.to_string()}")
        print(f"\n  前 5 筆:\n{df.head().to_string()}")
        print(f"\n  最後 5 筆:\n{df.tail().to_string()}")
    except Exception as e:
        print(f"  讀取失敗: {e}")
        cleanup(tmp_path)
        return
    input(">>> 按 Enter 繼續...\n")

    # Step 3: 轉換日期
    print("[Step 3] 轉換日期欄位...")
    df["Year-Month"] = pd.to_datetime(df["Year-Month"], format="%Y-%m")
    df.set_index("Year-Month", inplace=True)
    print(f"  Index type: {type(df.index).__name__}")
    print(f"  日期範圍: {df.index.min()} ~ {df.index.max()}")
    print(f"  總筆數: {len(df)}")
    input(">>> 按 Enter 繼續...\n")

    # Step 4: 測試各 symbol
    for symbol, column in _SYMBOL_MAP.items():
        print(f"\n[Step 4] 測試 symbol: {symbol}")
        result = df[[column]].rename(columns={column: "value"})
        result["value"] = pd.to_numeric(result["value"], errors="coerce")
        print(f"  欄位: {column}")
        print(f"  非空筆數: {result['value'].notna().sum()}")
        print(f"  最新值: {result['value'].iloc[0]:,.0f}")
        print(f"  平均值: {result['value'].mean():,.0f}")
        print(f"  最大值: {result['value'].max():,.0f} ({result['value'].idxmax()})")
        print(f"  最小值: {result['value'].min():,.0f} ({result['value'].idxmin()})")
        print(f"\n  最近 6 筆:\n{result.head(6).to_string()}")
        input(">>> 按 Enter 繼續...\n")

    # Step 5: 測試日期過濾
    print("[Step 5] 測試日期過濾 (2024-01 ~ 2024-06)...")
    filtered = df[(df.index >= pd.Timestamp("2024-01")) & (df.index <= pd.Timestamp("2024-06"))]
    print(f"  過濾後筆數: {len(filtered)}")
    print(f"  日期範圍: {filtered.index.min()} ~ {filtered.index.max()}")
    print(f"\n{filtered.head().to_string()}")
    input(">>> 按 Enter 繼續...\n")

    # Step 6: 測試 query API
    print("[Step 6] 測試 query API (dataframe)...")
    try:
        from financial_data_query import query
        result = query("finra_margin", "debit_balances", start="2024-01", end="2024-06", output="dataframe")
        print(f"  query() 回傳 type: {type(result).__name__}")
        print(f"  筆數: {len(result)}")
        print(f"\n{result.to_string()}")
    except Exception as e:
        print(f"  query() 失敗: {e}")

    print("\n[Step 7] 測試 query API (json 預設)...")
    try:
        result_json = query("finra_margin", "debit_balances", start="2024-01", end="2024-06")
        print(f"  query() 回傳 type: {type(result_json).__name__}")
        print(f"  keys: {list(result_json.keys())}")
        print(f"  筆數: {len(result_json['debit_balances'])}")
        print(f"  第一筆: {result_json['debit_balances'][0]}")
    except Exception as e:
        print(f"  query() 失敗: {e}")
    input(">>> 按 Enter 繼續...\n")

    # Step 8: 清理
    print(f"\n[Step 8] 清理暫存檔案...")
    cleanup(tmp_path)


def cleanup(path):
    if os.path.exists(path):
        os.unlink(path)
        print(f"  已刪除: {path}")
    else:
        print(f"  檔案不存在: {path}")


if __name__ == "__main__":
    main()
