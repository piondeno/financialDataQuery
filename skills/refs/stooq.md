# Stooq (`"stooq"`)

Stooq 歷史股價資料。使用 Selenium 網頁爬蟲，需要 Chrome 瀏覽器。支援 CAPTCHA 自動識別（本地 LLM）。

## 安裝

```bash
pip install -e ".[stooq]"
```

需要 Chrome 瀏覽器安裝在系統中。

## 參數

| 參數 | 說明 |
|------|------|
| `symbol` | Stooq 商品代號（見下方常見代號） |
| `frequency` | `"1d"`（日）, `"1wk"`（周）, `"1mo"`（月）, `"3mo"`（季）, `"1y"`（年） |
| `sub_field` | `"Open"`, `"High"`, `"Low"`, `"Close"`, `"Volume"` |

## 商品代號格式

| 市場 | 後綴 | 範例 |
|------|------|------|
| 美股 | `.us` | `"aapl.us"` |
| 美股（舊格式）| 無後綴 | `"aapl"` |
| 指數 | `.c` | `"sp500.c"`, `"dx.c"`（美元指數） |
| 匯率 | `.f` | `"usdeurf.f"` |
| 期貨 | `.cf` | `"gold.cf"` |
| 加密貨幣 | `.cc` | `"btcusd.cc"` |

## 使用範例

```python
from financial_data_query import query

# 查詢美股（批量查詢共用瀏覽器，效率較高）
result = query("stooq", ["aapl.us", "tsla.us", "msft.us"], start="2024-01-01", end="2024-12-31", frequency="1d")

# 查詢美元指數
result = query("stooq", "dx.c", frequency="1wk")

# 查詢黃金期貨
result = query("stooq", "gold.cf", start="2024-01-01", frequency="1mo")

# 查詢比特幣
result = query("stooq", "btcusd.cc", frequency="1d")
```

## 回傳欄位

`date`, `open`, `high`, `low`, `close`, `volume`

## 注意事項

- 批量查詢會共用同一個瀏覽器實例，比逐個查詢快得多
- CAPTCHA 識別需要本地 LLM（預設 `localhost:12345`，model `qwen3.5-9b`）
- 爬蟲速度較慢，每次查詢約需數秒
