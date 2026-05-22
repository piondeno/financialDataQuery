# Financial Data Query — 使用方式

統一金融資料查詢 API。所有資料來源共用同一個 `query()` 函數。

## 核心 API

```python
from financial_data_query import query

result = query(source, symbol, start=None, end=None, sub_field=None, frequency=None, output="json", use_cache=True)
```

| 參數 | 類型 | 說明 |
|------|------|------|
| `source` | `str` | 資料來源名稱 |
| `symbol` | `str` | `list[str]` | 商品代號，或清單進行批量查詢 |
| `start` | `str` | 開始日期 `YYYY-MM-DD`（部分來源支援 `YYYY-MM`） |
| `end` | `str` | 結束日期 `YYYY-MM-DD` |
| `sub_field` | `str` | 指定回傳欄位 |
| `frequency` | `str` | 資料頻率 |
| `output` | `str` | `"json"`（預設）或 `"dataframe"` |
| `use_cache` | `bool` | 記憶體快取，預設 `True` |

## 回傳格式

- `output="json"` → `dict[str, list[dict]]`，key 為 symbol，value 為記錄列表（每筆含 `date` 欄位）
- `output="dataframe"` → `pd.DataFrame`（單查詢）或含 `Symbol` 欄位的合併 DataFrame（批量查詢）

## 工具函數

```python
from financial_data_query import list_sources, clear_cache, register_source

list_sources()   # 列出所有已註冊的資料來源
clear_cache()    # 清除記憶體快取
```

## 錯誤處理

```python
from financial_data_query.errors import DataSourceError, DataSourceNotFoundError, ConfigError, FetchError

try:
    result = query("yahoo", "AAPL")
except DataSourceError as e:
    print(f"查詢失敗: {e}")
```

| 例外 | 觸發條件 |
|------|----------|
| `DataSourceNotFoundError` | 未知的 source 名稱 |
| `ConfigError` | API key 或設定缺失 |
| `FetchError` | 網路請求失敗或 API 錯誤 |

## 安裝與設定

```bash
# 基本安裝
pip install -e .

# Stooq / tw_eco / tw_pmi / macroMicro（需要 Chrome 瀏覽器）
pip install -e ".[stooq]"

# FINRA Margin
pip install -e ".[finra_margin]"

# ICI Fund Flows
pip install -e ".[ici]"
```

FRED 需要 API key，在專案根目錄建立 `.env`：
```
FRED_API_KEY=your_key_here
```

## 資料來源速查

| Source | 說明 | 需 API Key | 需瀏覽器 | 詳細文件 |
|--------|------|:----------:|:-------:|----------|
| `yahoo` | Yahoo Finance 股價 | 否 | 否 | [refs/yahoo.md](refs/yahoo.md) |
| `fred` | FRED 經濟指標 | 是 | 否 | [refs/fred.md](refs/fred.md) |
| `stooq` | Stooq 歷史股價 | 否 | 是 | [refs/stooq.md](refs/stooq.md) |
| `finra_margin` | FINRA 融資統計 | 否 | 否 | [refs/finra_margin.md](refs/finra_margin.md) |
| `ici` | ICI 基金資金流量 | 否 | 否 | [refs/ici.md](refs/ici.md) |
| `tw_eco` | 台灣 NCD 經濟指標 | 否 | 是 | [refs/tw_eco.md](refs/tw_eco.md) |
| `tw_pmi` | 台灣 NCD PMI | 否 | 是 | [refs/tw_pmi.md](refs/tw_pmi.md) |
| `macroMicro` | MacroMicro 經濟數據 | 否 | 是 | [refs/macroMicro.md](refs/macroMicro.md) |
| `usTreasuryApi` | 美國財政部公債拍賣 | 否 | 否 | [refs/usTreasuryApi.md](refs/usTreasuryApi.md) |
| `multpl` | Multpl S&P 500 估值指標 | 否 | 否 | [refs/multpl.md](refs/multpl.md) |

## 使用模式

1. **確定需要的資料來源** — 根據上方速查表選擇 source
2. **查閱對應的 refs 文件** — 確認可用 symbols、參數、安裝要求
3. **呼叫 `query()`** — 單筆或批量查詢
4. **處理結果** — JSON 格式適合 AI 模型，DataFrame 適合進一步分析

## 擴充自訂資料來源

```python
from financial_data_query import register_source
from financial_data_query.base import DataSourceFetcher
import pandas as pd

class MyFetcher(DataSourceFetcher):
    source_name = "my_source"

    def fetch(self, symbol, start=None, end=None, sub_field=None, frequency=None) -> pd.DataFrame:
        return pd.DataFrame(...)

register_source(MyFetcher)
```
