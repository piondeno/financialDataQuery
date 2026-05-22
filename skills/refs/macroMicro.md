# MacroMicro (`"macroMicro"`)

MacroMicro 宏觀經濟數據。使用 Selenium 從 Highcharts 圖表提取數據，需要 Chrome 瀏覽器。

資料來源: https://www.macromicro.me

## 安裝

```bash
pip install -e ".[stooq]"
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

已註冊的 symbol 可查閱專案根目錄的 `.macroMicro_links.json` 或 README.md 中的 MacroMicro 章節。

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
