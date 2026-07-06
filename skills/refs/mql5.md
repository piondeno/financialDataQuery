# MQL5 經濟日曆 (`"mql5"`)

MQL5 經濟日曆 PMI 數據，含今值/預測值/前值。免 API key，無需瀏覽器。

## 安裝

無需額外安裝。

## 支援商品

| Symbol | 說明 |
|--------|------|
| `eu_markit_composite_pmi` | 歐元區 Markit 綜合 PMI |
| `eu_markit_manufacturing_pmi` | 歐元區 Markit 製造業 PMI |
| `china_caixin_composite_pmi` | 中國財新綜合 PMI |
| `china_manufacturing_pmi` | 中國製造業 PMI |
| `china_caixin_manufacturing_pmi` | 中國財新製造業 PMI |
| `japan_markit_composite_pmi` | 日本 Markit 綜合 PMI |
| `brazil_markit_composite_pmi` | 巴西 Markit 綜合 PMI |
| `aus_cba_composite_pmi` | 澳洲 CBA 綜合 PMI |
| `us_markit_composite_pmi` | 美國 Markit 綜合 PMI |
| `us_markit_manufacturing_pmi` | 美國 Markit 製造業 PMI |
| `us_ism_manufacturing_pmi` | 美國 ISM 製造業 PMI |

## 使用範例

```python
from financial_data_query import query

# 查詢歐元區綜合 PMI
result = query("mql5", "eu_markit_composite_pmi")

# 指定日期範圍
result = query("mql5", "eu_markit_composite_pmi", start="2024-01-01", end="2024-12-31")

# 批量查詢多個國家（自動間隔 2 秒避免限流）
result = query("mql5", ["eu_markit_composite_pmi", "china_caixin_composite_pmi", "japan_markit_composite_pmi"])
```

## 回傳欄位

| 欄位 | 說明 |
|------|------|
| `date` | 發布日期 |
| `actual` | 今值（實際公布值） |
| `forecast` | 預測值 |
| `previous` | 前值 |

```python
# 查詢歐元區綜合 PMI
result = query("mql5", "eu_markit_composite_pmi")
# {'date': '2025-01-03', 'actual': 48.5, 'forecast': 49.0, 'previous': 47.8}
```

## 注意事項

- 部分日期的 `actual`、`forecast`、`previous` 可能為 `NaN`（尚未公布或無數據）
- 批量查詢時自動加入 2 秒延遲，避免被 MQL5 限流
- 回傳 JSON 時 `NaN` 值顯示為 `null`
- 資料範圍約 10 年歷史，每月更新
