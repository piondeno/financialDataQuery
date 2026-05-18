# MacroMicro 資料來源設計

## 概述

新增 MacroMicro (macromicro.me) 作為金融資料查詢來源。由於 MacroMicro 的商品名稱與 URL 對應關係不規則，需要額外機制讓使用者建立 symbol → URL 的映射關係。

## 檔案結構

```
src/financial_data_query/sources/macroMicro.py   # MacroMicroFetcher + macroMicroSymbolLinkConnect
.macroMicro_links.json                            # symbol → URL 映射檔（使用者維護）
```

## 映射管理

### `macroMicroSymbolLinkConnect(symbol, url, description)`

公開函數，用於建立或更新 symbol 映射：

- **輸入：** symbol（字串）、url（完整 URL）、description（說明文字）
- **行為：**
  - 將映射寫入 `.macroMicro_links.json`（專案根目錄）
  - 自動更新 README.md 中 `<!-- MACROMICRO_SYMBOLS_START -->` 到 `<!-- MACROMICRO_SYMBOLS_END -->` 表格區塊
  - symbol 已存在時覆蓋更新
- **JSON 格式：**
  ```json
  {
    "china-reverse-repo-rate-7-day": {
      "url": "https://www.macromicro.me/series/23233/china-reverse-repo-rate-7-day",
      "description": "中國7天期逆回購利率"
    }
  }
  ```

### README 更新機制

`macroMicroSymbolLinkConnect` 在 README.md 中尋找標記區塊，自動重新生成 Markdown 表格。無標記時在 MacroMicro 章節自動建立。

## MacroMicroFetcher

### 基本設定

- `source_name = "macroMicro"`
- 繼承 `DataSourceFetcher`
- 依賴 `undetected-chromedriver` + Selenium

### `fetch(symbol, start, end, sub_field, frequency)`

1. 從 `.macroMicro_links.json` 查找 symbol 對應 URL；不存在則拋出 `FetchError`
2. 開啟 Selenium 瀏覽器，訪問 URL
3. 等待頁面載入（`time.sleep(3)`）
4. 透過 `driver.execute_script` 讀取 `Highcharts.charts[0].series[0].data`
5. 將時間戳（毫秒 UTC）轉換為 UTC+8 台灣時間
6. 依 `start`/`end` 過濾
7. 回傳 DatetimeIndex DataFrame（欄位：`value`）

### `batch_fetch(symbols, start, end, sub_field, frequency)`

共用單一瀏覽器視窗，依序訪問各 symbol 對應 URL 抓取資料，回傳 `dict[str, pd.DataFrame]`。

### 時間處理

- MacroMicro 圖表時間戳為 Unix 毫秒（UTC）
- 轉換公式：`datetime.fromtimestamp(0) + timedelta(seconds=row['x']/1000 - 8*60*60)`
- 結果為 UTC+8 台灣時間

### 資料格式

Highcharts 資料點格式：`[{x: <timestamp_ms>, y: <value>}, ...]`
轉換為 DataFrame：
- index: DatetimeIndex（UTC+8）
- columns: `["value"]`

## 錯誤處理

| 情境 | 錯誤 |
|------|------|
| symbol 未在映射中 | `FetchError("找不到 symbol 'xxx'。請先執行 macroMicroSymbolLinkConnect() 建立映射")` |
| URL 無法存取 | `FetchError("無法存取 MacroMicro 頁面: <url>")` |
| 圖表資料為空 | `FetchError("頁面中找不到 Highcharts 圖表資料")` |
| JSON 映射檔損毀 | `FetchError("映射檔 .macroMicro_links.json 格式錯誤")` |
| Selenium 依賴未安裝 | `FetchError("undetected-chromedriver 未安裝...")` |

## 註冊

在 `sources/__init__.py` 中以 try/except 註冊 `MacroMicroFetcher`，依賴未安裝時靜默跳過。

## 測試

- `macroMicroSymbolLinkConnect` 建立/覆蓋映射，寫入 JSON
- README 表格區塊自動更新
- Fetcher 從 JSON 讀取 URL，mock 瀏覽器抓取 Highcharts 資料
- 時間戳正確轉換為 UTC+8
- Batch fetch 共用單一瀏覽器
- symbol 不存在時拋出正確錯誤
- 映射檔不存在時回傳空映射
- Fetcher 正確註冊到 Registry

## 使用範例

```python
# 建立映射
from financial_data_query.sources.macroMicro import macroMicroSymbolLinkConnect

macroMicroSymbolLinkConnect(
    "china-reverse-repo-rate-7-day",
    "https://www.macromicro.me/series/23233/china-reverse-repo-rate-7-day",
    "中國7天期逆回購利率"
)

# 查詢
from financial_data_query import query

result = query("macroMicro", "china-reverse-repo-rate-7-day")
# {"china-reverse-repo-rate-7-day": [{"date": "2024-01-02", "value": 1.8}, ...]}

# 批量查詢
result = query("macroMicro", ["symbol1", "symbol2"])
```
