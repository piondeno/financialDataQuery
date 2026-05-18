# Financial Data Query

Python 金融資料查詢函式庫，提供統一介面查詢不同資料來源的金融數據，預設回傳 JSON 格式方便 AI 模型使用。

## 安裝

```bash
pip install -e .
```

**要求：** Python 3.10+

## 快速開始

```python
from financial_data_query import query

# 單一查詢 — 回傳 JSON
result = query("yahoo", "AAPL")
# {"aapl": [{"date": "2024-01-02", "open": 185.0, "high": 187.0, ...}, ...]}

# 批量查詢 — 共用瀏覽器 (Stooq)
result = query("stooq", ["AAPL", "TSLA", "MSFT"])
# {"aapl": [...], "tsla": [...], "msft": [...]}

# 保留 DataFrame 格式
df = query("yahoo", "AAPL", output="dataframe")
# pd.DataFrame with DatetimeIndex
```

## API

### `query(source, symbol, start=None, end=None, sub_field=None, frequency=None, output="json", use_cache=True)`

| 參數 | 類型 | 說明 |
|------|------|------|
| `source` | `str` | 資料來源名稱：`"yahoo"`, `"fred"`, `"stooq"`, `"finra_margin"`, `"ici"` |
| `symbol` | `str \| list[str]` | 商品代碼，或代號清單進行批量查詢 |
| `start` | `str` | 開始日期 `YYYY-MM-DD`，可選 |
| `end` | `str` | 結束日期 `YYYY-MM-DD`，可選 |
| `sub_field` | `str` | 指定回傳欄位，可選 |
| `frequency` | `str` | 資料頻率，可選 |
| `output` | `str` | 輸出格式：`"json"`（預設）或 `"dataframe"` |
| `use_cache` | `bool` | 是否使用記憶體快取，預設 `True` |

**回傳：**
- `output="json"` → `dict[str, list[dict]]`
- `output="dataframe"` → `pd.DataFrame`

### JSON 格式

```json
{
  "aapl": [
    {"date": "2024-01-02", "open": 185.0, "high": 187.0, "low": 184.0, "close": 186.0, "volume": 52000000},
    {"date": "2024-01-03", "open": 186.5, "high": 188.0, "low": 185.0, "close": 187.0, "volume": 48000000}
  ],
  "tsla": [
    {"date": "2024-01-02", "open": 240.0, "high": 245.0, "low": 238.0, "close": 243.0, "volume": 95000000}
  ]
}
```

### 其他公開函數

```python
from financial_data_query import list_sources, register_source, clear_cache

# 列出所有已註冊的資料來源
list_sources()  # ['yahoo', 'fred', 'stooq', 'finra_margin', 'ici']

# 清除記憶體快取
clear_cache()
```

## 支援的資料來源

### Yahoo Finance (`"yahoo"`)

- 底層：`yfinance`
- 免 API key
- `sub_field` 支援：`open`, `high`, `low`, `close`, `volume`, `adjclose`

```python
result = query("yahoo", "AAPL", frequency="daily")
```

### FRED (`"fred"`)

- 底層：FRED REST API
- 需要 API key（免費申請：https://fred.stlouisfed.org/docs/api/api_key.html）

```python
result = query("fred", "CPIAUCSL")
```

### Stooq (`"stooq"`)

- 底層：`undetected_chromedriver` + Selenium 網頁爬蟲
- 免 API key，需要 Chrome 瀏覽器
- 支援 CAPTCHA 自動識別（本地 LLM）
- 批量查詢共用單一瀏覽器，節省開關時間

```python
# 安裝額外依賴
pip install -e ".[stooq]"

# 批量查詢 — 共用一個瀏覽器
result = query("stooq", ["dx.c", "sp500.c"], start="2024-01-01", end="2024-12-31", frequency="1d")
```

**頻率參數：** `1d`（日）, `1wk`（周）, `1mo`（月）, `3mo`（季）, `1y`（年）

### FINRA Margin Statistics (`"finra_margin"`)

- 底層：直接下載 FINRA 發布的 Excel 檔案
- 免 API key
- 資料來源：https://www.finra.org/margin-statistics
- 資料範圍：1997-01 至今，每月更新

**Symbols：**

| Symbol | 說明 |
|--------|------|
| `debit_balances` | 客戶信貸 (Debit Balances in Customers' Securities Margin Accounts) |
| `free_credit_cash` | 現金賬戶 (Free Credit Balances in Customers' Cash Accounts) |
| `free_credit_margin` | 融資賬戶 (Free Credit Balances in Customers' Securities Margin Accounts) |

```python
# 安裝額外依賴
pip install -e ".[finra_margin]"

# 查詢客戶信貸
result = query("finra_margin", "debit_balances")

# 指定日期範圍
result = query("finra_margin", "free_credit_cash", start="2024-01", end="2024-06")

# 批量查詢多個指標
result = query("finra_margin", ["debit_balances", "free_credit_margin"])
```

### ICI Fund Flows (`"ici"`)

- 底層：直接下載 ICI 發布的 XLS 檔案
- 免 API key
- 資料來源：Investment Company Institute
- 資料範圍：2024-01 至今，每週更新

**Symbols：**

| Symbol | 說明 |
|--------|------|
| `mf_total` | 共同基金總淨現金流 |
| `mf_equity_total` | 股票型基金合計 |
| `mf_equity_domestic_total` | 國內股票型基金合計 |
| `mf_equity_domestic_large` | 國內大型股 |
| `mf_equity_domestic_mid` | 國內中型股 |
| `mf_equity_domestic_small` | 國內小型股 |
| `mf_equity_domestic_multi` | 國內多類股 |
| `mf_equity_domestic_other` | 國內其他 |
| `mf_equity_world_total` | 全球股票型基金合計 |
| `mf_equity_world_developed` | 已開發市場 |
| `mf_equity_world_emerging` | 新興市場 |
| `mf_hybrid` | 混合型基金 |
| `mf_bond_total` | 債券型基金合計 |
| `mf_bond_taxable_total` | 課稅債券合計 |
| `mf_bond_taxable_investment` | 投資等級 |
| `mf_bond_taxable_highyield` | 高收益 |
| `mf_bond_taxable_government` | 政府債券 |
| `mf_bond_taxable_multisector` | 多部門 |
| `mf_bond_taxable_global` | 全球債券 |
| `mf_bond_municipal` | 地方政府債券 |
| `etf_total` | ETF 總淨發行量 |
| `etf_equity_total` | 股票型 ETF 合計 |
| `etf_equity_domestic` | 國內股票型 ETF |
| `etf_equity_world` | 全球股票型 ETF |
| `etf_hybrid` | 混合型 ETF |
| `etf_bond_total` | 債券型 ETF 合計 |
| `etf_bond_taxable` | 課稅債券型 ETF |
| `etf_bond_municipal` | 地方政府債券型 ETF |
| `etf_commodity` | 商品型 ETF |
| `combined_total` | 總長期基金+ETF 資金流量 |
| `combined_equity_total` | 股票型基金+ETF 合計 |
| `combined_equity_domestic` | 國內股票型基金+ETF |
| `combined_equity_world` | 全球股票型基金+ETF |
| `combined_hybrid` | 混合型基金+ETF |
| `combined_bond_total` | 債券型基金+ETF 合計 |
| `combined_bond_taxable` | 課稅債券型基金+ETF |
| `combined_bond_municipal` | 地方政府債券型基金+ETF |
| `combined_commodity` | 商品型基金+ETF |

```python
# 安裝額外依賴
pip install -e ".[ici]"

# 查詢共同基金總淨現金流
result = query("ici", "mf_total")

# 查詢 ETF 總淨發行量
result = query("ici", "etf_total")

# 指定日期範圍
result = query("ici", "mf_equity_total", start="2024-01-01", end="2024-06-30")

# 批量查詢
result = query("ici", ["mf_total", "etf_total", "combined_total"])
```

## 設定

### FRED API Key

專案根目錄建立 `.env` 檔案：

```bash
FRED_API_KEY=your_api_key_here
```

`.env` 已加入 `.gitignore`，不會被提交到版本控制。也可以透過環境變數設定：

```bash
export FRED_API_KEY=your_api_key_here
```

### Stooq CAPTCHA 識別

Stooq 需要本地 LLM 識別 CAPTCHA。預設使用 `http://localhost:12345/v1`（llama.cpp API），model `qwen3.5-9b`。

## 擴充自訂資料來源

繼承 `DataSourceFetcher` 並註冊：

```python
from financial_data_query import register_source
from financial_data_query.base import DataSourceFetcher
import pandas as pd

class MyFetcher(DataSourceFetcher):
    source_name = "my_source"

    def fetch(self, symbol, start=None, end=None, sub_field=None, frequency=None) -> pd.DataFrame:
        # 實作你的資料查詢邏輯
        return pd.DataFrame(...)

    # 可選：覆寫 batch_fetch 以優化批量查詢
    def batch_fetch(self, symbols, start=None, end=None, sub_field=None, frequency=None):
        # 預設逐個呼叫 fetch()，可覆寫以共用資源
        return super().batch_fetch(symbols, start=start, end=end, sub_field=sub_field, frequency=frequency)

register_source(MyFetcher)

# 現在可以使用
result = query("my_source", "SYMBOL")
```

## 錯誤處理

| 例外類別 | 觸發條件 |
|----------|----------|
| `DataSourceError` | 所有資料來源相關錯誤的基底類 |
| `DataSourceNotFoundError` | 未知的資料來源名稱 |
| `ConfigError` | API key 或設定缺失 |
| `FetchError` | 網路請求失敗或 API 回傳錯誤 |

```python
from financial_data_query import query
from financial_data_query.errors import DataSourceError

try:
    result = query("yahoo", "INVALID_SYMBOL")
except DataSourceError as e:
    print(f"查詢失敗: {e}")
```

## 開發

```bash
# 安裝開發依賴
pip install -e ".[dev]"

# 執行測試
pytest tests/ -v
```
