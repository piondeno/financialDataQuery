# Financial Data Query

Python 金融資料查詢函式庫，提供統一介面查詢不同資料來源的金融數據，回傳標準化的 pandas DataFrame。

## 安裝

```bash
pip install -e .
```

**要求：** Python 3.10+

## 快速開始

```python
from financial_data_query import query

# Yahoo Finance — 查詢 Apple 股價
df = query("yahoo", "AAPL")

# 帶時間範圍
df = query("yahoo", "AAPL", start="2024-01-01", end="2024-12-31")

# FRED — 查詢美國 GDP 數據
df = query("fred", "GDP")
```

## API

### `query(source, symbol, start=None, end=None, sub_field=None, use_cache=True)`

| 參數 | 類型 | 說明 |
|------|------|------|
| `source` | `str` | 資料來源名稱：`"yahoo"` 或 `"fred"` |
| `symbol` | `str` | 商品代碼（Yahoo 格式如 `AAPL`，或 FRED 系列代碼如 `GDP`） |
| `start` | `str` | 開始日期，格式 `YYYY-MM-DD`，可選 |
| `end` | `str` | 結束日期，格式 `YYYY-MM-DD`，可選 |
| `sub_field` | `str` | 指定回傳的欄位，可選（Yahoo 支援：`open`, `high`, `low`, `close`, `volume`, `adjclose`） |
| `use_cache` | `bool` | 是否使用記憶體快取，預設 `True` |

**回傳：** `pd.DataFrame`，索引為 `DatetimeIndex`

### 其他公開函數

```python
from financial_data_query import list_sources, register_source, clear_cache

# 列出所有已註冊的資料來源
list_sources()  # ['yahoo', 'fred']

# 清除記憶體快取
clear_cache()
```

## 支援的資料來源

### Yahoo Finance (`"yahoo"`)

- 底層：`yfinance`
- 免 API key
- `sub_field` 支援：`open`, `high`, `low`, `close`, `volume`, `adjclose`（預設回傳全部欄位）

```python
# 只查詢收盤價
df = query("yahoo", "AAPL", sub_field="close")
```

### FRED (`"fred"`)

- 底層：FRED REST API
- 需要 API key（免費申請：https://fred.stlouisfed.org/docs/api/api_key.html）

```python
# 查詢消費者物價指數
df = query("fred", "CPIAUCSL")
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

## 擴充自訂資料來源

繼承 `DataSourceFetcher` 並註冊：

```python
from financial_data_query import register_source
from financial_data_query.base import DataSourceFetcher
import pandas as pd

class MyFetcher(DataSourceFetcher):
    source_name = "my_source"

    def fetch(self, symbol, start=None, end=None, sub_field=None) -> pd.DataFrame:
        # 實作你的資料查詢邏輯
        return pd.DataFrame(...)

register_source(MyFetcher)

# 現在可以使用
df = query("my_source", "SYMBOL")
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
    df = query("yahoo", "INVALID_SYMBOL")
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
