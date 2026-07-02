from financial_data_query import query

print("=" * 60)
print("ICI Fund Flows 測試腳本")
print("=" * 60)

# 測試 1：共同基金總淨現金流
print("\n1. mf_total (共同基金總淨現金流)")
result = query("ici", "mf_total", start="2024-06", end="2024-08")
for row in result["mf_total"]:
    print(f"   {row['date']}: {row['value']:,.0f}")

# 測試 2：ETF 總淨發行量
print("\n2. etf_total (ETF 總淨發行量)")
result = query("ici", "etf_total", start="2024-06", end="2024-08")
for row in result["etf_total"]:
    print(f"   {row['date']}: {row['value']:,.0f}")

# 測試 3：合併數據
print("\n3. combined_total (總長期基金+ETF 資金流量)")
result = query("ici", "combined_total", start="2024-06", end="2024-08")
for row in result["combined_total"]:
    print(f"   {row['date']}: {row['value']:,.0f}")

# 測試 4：批量查詢
print("\n4. 批量查詢 [mf_total, etf_total, combined_total]")
result = query("ici", ["mf_total", "etf_total", "combined_total"], start="2024-11", end="2024-12")
for sym, rows in result.items():
    val = rows[0]["value"]
    print(f"   {sym}: {val:,.0f}")

# 測試 5：ETF 股票型
print("\n5. etf_equity_total (股票型 ETF 合計)")
result = query("ici", "etf_equity_total", start="2024-01", end="2024-03")
for row in result["etf_equity_total"]:
    print(f"   {row['date']}: {row['value']:,.0f}")

# 測試 6：共同基金債券
print("\n6. mf_bond_total (債券型基金合計)")
result = query("ici", "mf_bond_total", start="2024-01", end="2024-03")
for row in result["mf_bond_total"]:
    print(f"   {row['date']}: {row['value']:,.0f}")

print("\n" + "=" * 60)
print("測試完成")
print("=" * 60)
