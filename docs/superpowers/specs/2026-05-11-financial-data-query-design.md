# Financial Data Query Library — Design Spec

**Date:** 2026-05-11
**Status:** Approved

## Overview

Python 金融資料查詢函式庫，提供統一介面查詢不同資料來源的金融數據。初始支援 Yahoo Finance 與 FRED，架構支援未來擴充新資料來源。

**使用方式：**
```python
from financial_data_query import query

df = query("yahoo", "AAPL", start="2024-01-01", end="2024-12-31")
df = query("fred", "GDP")
```

## Architecture

策略模式 + 註冊表。每個資料來源實作統一的抽象基類 `DataSourceFetcher`，透過 `Registry` 管理註冊與路由。

### Project Structure

```
financialDataQuery/
├── src/
│   └── financial_data_query/
│       ├── __init__.py            # 公開 API: query(), register_source()
│       ├── base.py                # DataSourceFetcher 抽象基類
│       ├── registry.py            # 資料來源註冊表
│       ├── sources/
│       │   ├── __init__.py
│       │   ├── yahoo.py           # Yahoo Finance 實作
│       │   └── fred.py            # FRED 實作
│       ├── cache.py               # 記憶體 LRU 快取
│       └── config.py              # API key / 設定管理
├── tests/
│   ├── test_yahoo.py
│   ├── test_fred.py
│   └── test_cache.py
├── .env.example
├── pyproject.toml
└── .gitignore
```

## Core API

### Unified Query Function

```python
def query(
    source: str,
    symbol: str,
    start: str | None = None,
    end: str | None = None,
    sub_field: str | None = None,
    use_cache: bool = True,
) -> pd.DataFrame:
    ...
```

| 參數 | 說明 |
|------|------|
| `source` | 資料來源名稱，如 `"yahoo"`, `"fred"` |
| `symbol` | 商品代碼（Yahoo 格式或 FRED 系列代碼） |
| `start` | 開始日期，格式 `YYYY-MM-DD`，可選 |
| `end` | 結束日期，格式 `YYYY-MM-DD`，可選 |
| `sub_field` | 子項目欄位，可選 |
| `use_cache` | 是否使用快取，預設 `True` |

**回傳：** pandas DataFrame，索引為 `DatetimeIndex`

### DataSourceFetcher Abstract Base Class

```python
class DataSourceFetcher(ABC):
    source_name: str

    @abstractmethod
    def fetch(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        sub_field: str | None = None,
    ) -> pd.DataFrame: ...

    def validate_config(self) -> bool: ...
```

### Registry

```python
Registry.register(YahooFetcher)   # source_name = "yahoo"
Registry.register(FredFetcher)    # source_name = "fred"
```

查詢時由 `query()` 透過註冊表查找對應的 Fetcher 執行。

## Data Sources

### Yahoo Finance (`YahooFetcher`)

- 底層：`yfinance`
- `sub_field` 支援值：`open`, `high`, `low`, `close`, `volume`, `adjclose`
- 預設回傳全部欄位
- 商品代碼：Yahoo 格式（`AAPL`, `^GSPC`）

### FRED (`FredFetcher`)

- 底層：FRED API（HTTP 請求）
- API key 從環境變數 `FRED_API_KEY` 讀取
- `sub_field`：目前留作未來擴充
- 商品代碼：FRED 系列代碼（`GDP`, `CPIAUCSL`）

## Error Handling

| 例外類別 | 觸發條件 |
|----------|----------|
| `DataSourceError` (基底) | 所有資料來源相關錯誤 |
| `DataSourceNotFoundError` | 未知的 `source` 名稱 |
| `ConfigError` | API key 或設定缺失 |
| `FetchError` | 網路請求失敗或 API 回傳錯誤 |

## Caching

- 記憶體 LRU 快取，預設上限 128 筆
- 快取 key：`(source, symbol, start, end, sub_field)`
- 提供 `cache.clear()` 手動清除
- `query(..., use_cache=False)` 可跳過快取

## Configuration

- API key 從環境變數讀取，支援 `.env` 檔案（`python-dotenv`）
- `.env.example` 提供範例：
  ```
  FRED_API_KEY=your_key_here
  ```
- `config.get_config(key)` 統一讀取，包含預設值與驗證
- **API key 絕不寫入程式碼或提交至版本控制**

## Testing

- 單元測試：mock API 回應，驗證資料解析與錯誤處理
- 快取測試：驗證 LRU 行為、上限、清除功能
- 擴充測試：註冊新 Fetcher 類，驗證路由正確性
