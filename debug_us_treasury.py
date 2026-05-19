#!/usr/bin/env python
"""US Treasury API 除錯測試腳本"""
import json
from financial_data_query import query


def main():
    # Step 1: 查詢 10 年期公債
    print("[Step 1] 查詢 10 年期公債 (2024-01 ~ 2024-03)...")
    result = query("usTreasuryApi", "note_10y", start="2024-01-01", end="2024-03-31")
    print(f"  筆數: {len(result['note_10y'])}")
    print(f"  欄位: {list(result['note_10y'][0].keys())}")
    print(f"  第一筆:\n{json.dumps(result['note_10y'][0], indent=2, default=str)}")
    input(">>> 按 Enter 繼續...")

    # Step 2: 查詢 13 週國庫券
    print("[Step 2] 查詢 13 週國庫券 (2024-01 ~ 2024-03)...")
    result = query("usTreasuryApi", "bill_13w", start="2024-01-01", end="2024-03-31")
    print(f"  筆數: {len(result['bill_13w'])}")
    print(f"  第一筆:\n{json.dumps(result['bill_13w'][0], indent=2, default=str)}")
    input(">>> 按 Enter 繼續...")

    # Step 3: 查詢 30 年期公債
    print("[Step 3] 查詢 30 年期公債 (2024-01 ~ 2024-03)...")
    result = query("usTreasuryApi", "bond_30y", start="2024-01-01", end="2024-03-31")
    print(f"  筆數: {len(result['bond_30y'])}")
    print(f"  第一筆:\n{json.dumps(result['bond_30y'][0], indent=2, default=str)}")
    input(">>> 按 Enter 繼續...")

    # Step 4: 查詢所有期限
    print("[Step 4] 查詢所有期限 (2024-01)...")
    result = query("usTreasuryApi", "allBond", start="2024-01-01", end="2024-01-31")
    print(f"  筆數: {len(result['allBond'])}")
    terms = set(r["security_term"] for r in result["allBond"])
    print(f"  包含期限: {sorted(terms)}")
    print(f"  第一筆:\n{json.dumps(result['allBond'][0], indent=2, default=str)}")
    input(">>> 按 Enter 繼續...")

    # Step 5: 批量查詢
    print("[Step 5] 批量查詢 [note_2y, note_10y, bond_30y]...")
    result = query(
        "usTreasuryApi",
        ["note_2y", "note_10y", "bond_30y"],
        start="2024-01-01",
        end="2024-03-31",
    )
    for symbol, records in result.items():
        print(f"  {symbol}: {len(records)} 筆")
    input(">>> 按 Enter 繼續...")

    # Step 6: DataFrame 格式
    print("[Step 6] DataFrame 格式輸出...")
    df = query(
        "usTreasuryApi",
        "note_10y",
        start="2024-01-01",
        end="2024-03-31",
        output="dataframe",
    )
    print(f"  Shape: {df.shape}")
    print(f"  Columns: {list(df.columns)}")
    print(f"\n  前 5 筆:\n{df.head()}")
    input(">>> 按 Enter 繼續...")

    # Step 7: 無效代號測試
    print("[Step 7] 無效代號測試...")
    try:
        query("usTreasuryApi", "invalid_symbol")
    except Exception as e:
        print(f"  錯誤訊息: {e}")
    input(">>> 按 Enter 繼續...")

    print("測試完成!")


if __name__ == "__main__":
    main()
