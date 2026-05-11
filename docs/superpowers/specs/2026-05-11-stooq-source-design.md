# Stooq 資料來源設計

**日期:** 2026-05-11  
**狀態:** 已批准

## 總覽

新增 `StooqFetcher` 資料來源，透過 undetected_chromedriver 操作 Stooq 網頁，下載 CSV 資料並回傳 pandas DataFrame。

## 架構

遵循現有 `DataSourceFetcher` 抽象類別模式，所有邏輯集中在單一檔案。

### 新增/修改檔案

| 檔案 | 類型 | 說明 |
|------|------|------|
| `src/financial_data_query/sources/stooq.py` | 新增 | StooqFetcher 核心實作 |
| `src/financial_data_query/sources/__init__.py` | 修改 | 註冊 StooqFetcher |
| `pyproject.toml` | 修改 | 新增 stooq optional dependency |

### 使用方式

```python
import financial_data_query as fdq

# 基本查詢
df = fdq.query("stooq", "dx.c")

# 指定日期範圍和頻率
df = fdq.query("stooq", "dx.c", start="2024-01-01", end="2024-12-31", frequency="1d")
```

## 核心流程

1. 建立 headless Chrome 瀏覽器實例（undetected_chromedriver）
2. 導航至 `https://stooq.com/q/d/?s={symbol}`
3. 等待頁面載入完成
4. 設定頻率按鈕（根據 frequency 參數）
5. 設定日期範圍（如果提供 start/end）
6. 點擊更新按鈕
7. 等待資料更新
8. 點擊下載 CSV 連結
9. 關閉瀏覽器
10. 用 pandas 解析 CSV，設定 DatetimeIndex
11. 刪除臨時 CSV 檔案
12. 回傳 DataFrame

## 參數對應

### frequency 參數

| 參數值 | Stooq 按鈕 |
|--------|-----------|
| `1d` | 日 |
| `1wk` | 周 |
| `1mo` | 月 |
| `3mo` | 季 |
| `1y` | 年 |

參數格式與 Yahoo Finance interval 保持一致。未指定時使用網頁預設。

### 日期設定

- **Start date:** 月份下拉選單 + 日期輸入 + 年份輸入
- **End date:** 月份下拉選單 + 日期輸入 + 年份輸入
- 未指定時不操作日期欄位，使用 Stooq 網頁預設範圍

### 選擇器策略

使用 CSS 選擇器（而非 XPath）定位頁面元素，基於元素的 `name`、`type`、`class` 等屬性。比絕對 XPath 更穩定，頁面結構微調時不易失效。

## 錯誤處理

| 場景 | 行為 |
|------|------|
| Chrome 瀏覽器未安裝 | `FetchError`，提示安裝 Chrome |
| 頁面載入超時 | `FetchError`，包含超時資訊 |
| 找不到元素 | `FetchError`，提示元素找不到 |
| CSV 下載失敗 | `FetchError` |
| 無資料返回 | `FetchError` |

## 資源清理

- `try/finally` 確保瀏覽器一定會關閉
- CSV 臨時檔案在 `finally` 中刪除
- 瀏覽器使用 headless 模式

## 超時設定

| 操作 | 超時 |
|------|------|
| 頁面載入 | 30 秒 |
| 元素等待 | 10 秒 |
| 下載等待 | 15 秒 |

## 依賴管理

瀏覽器相關依賴作為 optional dependency，不影響其他資料來源的使用：

```toml
[project.optional-dependencies]
stooq = [
    "undetected-chromedriver>=3.5",
    "selenium>=4.0",
]
```

## 測試策略

- 單元測試：mock Selenium WebDriver，測試參數轉換和 CSV 解析
- 不寫整合測試（需要真實瀏覽器環境）
- 驗證 frequency 參數和日期格式
