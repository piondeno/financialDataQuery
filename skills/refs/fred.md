# FRED (`"fred"`)

Federal Reserve Economic Data 經濟指標資料庫。需要 FRED API key。

## 安裝

基本安裝已包含，無需額外依賴。

## 設定

在專案根目錄 `.env` 檔案中設定：
```
FRED_API_KEY=your_key_here
```

或透過環境變數：
```bash
export FRED_API_KEY=your_key_here
```

免費申請 API key: https://fred.stlouisfed.org/docs/api/api_key.html

## 參數

| 參數 | 說明 |
|------|------|
| `symbol` | FRED 系列代號（如 `"CPIAUCSL"`, `"GDP"`, `"UNRATE"`） |
| `start` / `end` | 日期 `YYYY-MM-DD` |

`sub_field` 和 `frequency` 不適用。

## 使用範例

```python
from financial_data_query import query

# 查詢消費者物價指數
result = query("fred", "CPIAUCSL")

# 查詢 GDP
result = query("fred", "GDP", start="2020-01-01")

# 查詢失業率
result = query("fred", "UNRATE", start="2020-01-01", end="2024-12-31")

# 回傳 DataFrame
df = query("fred", "CPIAUCSL", output="dataframe")
```

## 回傳欄位

`date`, `value`

## 常見系列代號

| 代號 | 說明 |
|------|------|
| `CPIAUCSL` | 消費者物價指數（-all urban consumers） |
| `GDP` | 國內生產毛額 |
| `UNRATE` | 失業率 |
| `FEDFUNDS` | 聯邦基金利率 |
| `INDPRO` | 工業生產指數 |
| `T10YIEND` | 10年期公債收益率 |
