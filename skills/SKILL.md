---
name: financial-data-query
description: 統一金融資料查詢 API，支援 Yahoo Finance、FRED、Stooq、AkShare、MOEA、FINRA、ICI、台灣 NCD（tw_eco/tw_pmi）、MacroMicro、Zillow、OptionCharts、MQL5 等多個資料來源
---

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
| `use_cache` | `bool` | 啟用記憶體 + 磁碟快取，預設 `True` |

## 回傳格式

- `output="json"` → `dict[str, list[dict]]`，key 為 symbol，value 為記錄列表（每筆含 `date` 欄位）
- `output="dataframe"` → `pd.DataFrame`（單查詢）或含 `Symbol` 欄位的合併 DataFrame（批量查詢）

## 工具函數

```python
from financial_data_query import list_sources, clear_cache, clear_disk_cache, register_source

list_sources()   # 列出所有已註冊的資料來源
clear_cache()    # 清除記憶體快取
clear_disk_cache()  # 清除舊的磁碟快取（保留今天）
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

## 資料源與商品代號 查詢
<HARD-GATE>
使用文件， **refs/symbols_reference.md**，進行資料源與商品代號查詢
</HARD-GATE>

## 快取機制

所有資料來源皆啟用磁碟快取。資料首次下載時儲存完整歷史，後續查詢從快取截取日期範圍。

- 記憶體快取：同行程內的 LRU 快取（`clear_cache()` 清除）
- 磁碟快取：SQLite 檔，按日輪替，檔名 `YYYY-MM-DD.db`（`clear_disk_cache()` 清除舊檔）

## 使用模式

1. **確定需要的資料來源** — 根據上方速查表選擇 source
2. **查閱對應的 refs 文件** — 確認可用 symbols、參數、安裝要求
3. **呼叫 `query()`** — 單筆或批量查詢
4. **處理結果** — JSON 格式適合 AI 模型，DataFrame 適合進一步分析

