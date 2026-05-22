# Multpl (`"multpl"`)

Multpl 網站 S&P 500 估值與歷史數據。免 API key，免瀏覽器，基本安裝已包含。

資料來源: https://www.multpl.com
資料範圍: 1870 年至今（Shiller PE），每月/每季更新

## 安裝

基本安裝已包含，無需額外依賴。

## Symbols

| Symbol | 說明 | 頻率 |
|--------|------|------|
| `sp500_ps` | S&P 500 本銷比 (Price to Sales) | 季 |
| `sp500_div_yield` | S&P 500 殖利率 (Dividend Yield) | 月 |
| `sp500_pe` | S&P 500 本益比 (PE Ratio) | 月 |
| `shiller_pe` | Shiller 本益比 (CAPE) | 月 |
| `sp500_earn_yield` | S&P 500 盈餘收益率 (Earnings Yield) | 月 |
| `sp500_price` | S&P 500 歷史價格 (Historical Prices) | 月 |
| `sp500_earn_growth` | S&P 500 盈餘成長率 (Earnings Growth) | 季 |

## 回傳欄位

| 欄位 | 說明 |
|------|------|
| `value` | 數值（百分比欄位已去除 % 符號，回傳純數值） |

## 參數

| 參數 | 說明 |
|------|------|
| `start` / `end` | 日期 `YYYY-MM-DD` |

`sub_field`、`frequency` 不適用（單一 value 欄位，頻率由 symbol 決定）。

## 使用範例

```python
from financial_data_query import query

# 查詢 S&P 500 本益比
result = query("multpl", "sp500_pe")

# 查詢 Shiller PE
result = query("multpl", "shiller_pe", start="2000-01-01")

# 指定日期範圍
result = query("multpl", "sp500_div_yield", start="2020-01-01", end="2024-12-31")

# 批量查詢
result = query("multpl", ["sp500_pe", "shiller_pe", "sp500_div_yield"])
```

## 注意事項

- 每次查詢會即時抓取網頁，無快取機制
- 部分近期數據為估計值（† 標記），已自動清理
- `sp500_earn_growth` 回傳為百分比數值（例：16.87 表示 16.87%）
