# MacroMicro (`"macroMicro"`)

MacroMicro 宏觀經濟數據。使用 Selenium 從 Highcharts 圖表提取數據，需要 Chrome 瀏覽器。

資料來源: https://www.macromicro.me

## 安裝

```bash
pip install -e ".[macroMicro]"
```

## 建立 Symbol 映射

使用前必須先建立 symbol 和 MacroMicro URL 的映射。映射資料儲存在 `.macroMicro_links.json`。

```python
from financial_data_query.sources.macroMicro import macroMicroSymbolLinkConnect

# 只需輸入 URL，商品代號與描述會自動提取
macroMicroSymbolLinkConnect(
    "https://www.macromicro.me/series/23233/china-reverse-repo-rate-7-day"
)
```

或命令行執行：
```bash
python -c "from financial_data_query.sources.macroMicro import macroMicroSymbolLinkConnect; macroMicroSymbolLinkConnect('https://www.macromicro.me/series/23233/china-reverse-repo-rate-7-day')"
```

## Symbols

| Symbol | 說明 | 資料範圍 |
|--------|------|----------|
| `us-5year-cds` | 美國 5 年信用違約交換 (CDS) | — |
| `cn-dr007` | 中國銀行間債券質押式回購利率 DR007（7 天期） | — |
| `china-reverse-repo-rate-7-day` | 中國逆回購利率日數據 7 天期 | — |
| `ism-manufacturing-supplierdeliveries` | ISM 製造業 PMI - 供應商交貨指數 | 1985-01 ~ 至今（624 筆） |
| `ism-manufacturing-neworders` | ISM 製造業 PMI - 新訂單指數 | 1948-01 ~ 至今（159 筆） |
| `ism-manufacturing-customersinventories` | ISM 製造業 PMI - 客戶存貨指數 | 1997-01 ~ 至今（61 筆） |
| `ism-manufacturing-backlogoforders` | ISM 製造業 PMI - 未完成訂單指數 | 1993-01 ~ 至今（69 筆，半年頻） |
| `us-new-tenant-rent-index` | 美國新租客租金指數 | 2005-01 ~ 2025-07（31 筆，季頻） |
| `tw-inventories-sales-ratio-manufacturing` | 台灣製造業存貨率 | 1982-01 ~ 至今（91 筆，半年頻） |

## 參數

| 參數 | 說明 |
|------|------|
| `start` / `end` | 日期 `YYYY-MM-DD` |

`sub_field` 和 `frequency` 不適用。

## 使用範例

```python
from financial_data_query import query

# 查詢已註冊的指標
result = query("macroMicro", "china-reverse-repo-rate-7-day")

# ISM 製造業 PMI - 新訂單指數
df = query("macroMicro", "ism-manufacturing-neworders", output="dataframe")
#           value
# date            
# 1948-01-01  53.3
# 1948-07-01  50.4

# ISM 製造業 PMI - 客戶存貨指數
df = query("macroMicro", "ism-manufacturing-customersinventories", output="dataframe")

# 指定日期範圍
result = query("macroMicro", "cn-dr007", start="2024-01-01", end="2024-12-31")

# 批量查詢（共用瀏覽器）
result = query("macroMicro", ["china-reverse-repo-rate-7-day", "cn-dr007"])
```

## 回傳欄位

`date`, `value`

## 注意事項

- 必須先執行 `macroMicroSymbolLinkConnect()` 建立映射才能查詢
- 批量查詢會共用同一個瀏覽器實例
- 數據從網頁 Highcharts 圖表的 JavaScript 物件中提取
