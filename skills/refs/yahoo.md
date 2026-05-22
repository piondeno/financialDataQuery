# Yahoo Finance (`"yahoo"`)

Yahoo Finance 股價資料。底層使用 `yfinance`，免 API key，無需瀏覽器。

## 安裝

基本安裝已包含，無需額外依賴。

## 參數

| 參數 | 說明 |
|------|------|
| `symbol` | 股票代號（如 `"AAPL"`, `"TSLA"`, `"MSFT"`） |
| `frequency` | `"daily"`, `"weekly"`, `"monthly"` |
| `sub_field` | 指定欄位：`"open"`, `"high"`, `"low"`, `"close"`, `"volume"`, `"adjclose"` |

## 使用範例

```python
from financial_data_query import query

# 查詢最近股價
result = query("yahoo", "AAPL")

# 指定日期範圍與頻率
result = query("yahoo", "AAPL", start="2024-01-01", end="2024-06-30", frequency="weekly")

# 只回傳收盤價
result = query("yahoo", "AAPL", sub_field="close")

# 批量查詢
result = query("yahoo", ["AAPL", "TSLA", "MSFT"], start="2024-01-01")

# 回傳 DataFrame
df = query("yahoo", "AAPL", output="dataframe")
```

## 回傳欄位

`date`, `open`, `high`, `low`, `close`, `volume`, `adjclose`
